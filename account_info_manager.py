from typing import Union, Dict, Sequence, List
import time

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.rpc.responses import GetAccountInfoMaybeJsonParsedResp

from construct import Bytes, Int16ul, Int64ul
from construct import Struct

import logger
from consts import TOKEN_2022_PROGRAM_ID
from data_types.fee_config import FeeConfig, TransferFee
from errors import SolanaTransactionFetchError

PubkeyOrStr = Union[Pubkey, str]
DEFAULT_MAX_RETRIES = 5  # maximum number of times to retry get_confirmed_transaction call
DELAY_SECONDS = 0.2  # number of seconds to wait between calls to get_confirmed_transaction

PUBLIC_KEY_LAYOUT = Bytes(32)
TRANSFER_FEE_LAYOUT = Struct(
    'epoch' / Int64ul,
    'maximumFee' / Int64ul,
    'transferFeeBasisPoints' / Int16ul
)
FEE_CONFIG_LAYOUT = Struct(
    'transferFeeConfigAuthority' / PUBLIC_KEY_LAYOUT,
    'withdrawWithheldAuthority' / PUBLIC_KEY_LAYOUT,
    'withheldAmount' / Int64ul,
    'olderTransferFee' / TRANSFER_FEE_LAYOUT,
    'newerTransferFee' / TRANSFER_FEE_LAYOUT
)


class FeeConfigError(Exception):
    pass


class AccountInfoManager:
    def __init__(self, endpoint: str = 'https://api.mainnet-beta.solana.com'):
        self.client = AsyncClient(endpoint)
        self.account_info_dict: Dict[PubkeyOrStr, GetAccountInfoMaybeJsonParsedResp] = {}
        self.fee_config_dict: Dict[PubkeyOrStr, Union[FeeConfig, None]] = {}
        self.endpoint = endpoint
        self.logger = logger.get_logger(__name__, filename=f"{__name__}.log")

    async def get_account_info_json_parsed(
            self,
            accounts: Union[Pubkey, Sequence[Pubkey]],
            retries=DEFAULT_MAX_RETRIES
    ):
        acc_info_resps: Dict[str, Union[GetAccountInfoMaybeJsonParsedResp, None]] = {}
        if isinstance(accounts, PubkeyOrStr):
            accounts = [accounts]
        for index, account in enumerate(accounts):
            if isinstance(account, Pubkey):
                accounts[index] = str(account)

        for account in accounts:
            num_retries = retries
            while num_retries > 0:
                try:
                    if account in self.account_info_dict.keys():
                        acc_info_resp = self.account_info_dict[account]
                        acc_info_resps[account] = acc_info_resp
                        break

                    acc_info_resp = await self.client.get_account_info_json_parsed(account)
                    if acc_info_resp.value is not None:
                        self.account_info_dict[account] = acc_info_resp
                        acc_info_resps[account] = acc_info_resp
                        break
                except KeyError as e:
                    self.logger.debug(e)
                except Exception as e:
                    self.logger.error(
                        f"Failed to receive account info response from endpoint {self.endpoint}, account {account}, {e}",
                        exc_info=True,
                    )
                num_retries -= 1
                time.sleep(DELAY_SECONDS)
                self.logger.debug(
                    f"Retrying get_account_info fetch: {account} with endpoint {self.endpoint}"
                )

            if num_retries == 0:
                self.logger.error(
                    f"Error fetching get_account_info by account {account} from endpoint {self.endpoint}",
                    exc_info=True,
                )
                raise SolanaTransactionFetchError(f"Error fetching get_account_info "
                                                  f"by account {account} from endpoint {self.endpoint}")

        return acc_info_resps

    async def get_fee_config(self, address: PubkeyOrStr):
        if address in self.fee_config_dict.keys():
            return self.fee_config_dict[address]

        if isinstance(address, str):
            address = Pubkey.from_string(address)

        def _extract_extension_data(_bytes_data: list[int]):
            # copy from "@solana/spl-token" ts package
            MINT_SIZE, ACCOUNT_SIZE, MULTISIG_SIZE, ACCOUNT_TYPE_SIZE = 82, 165, 355, 1

            if (len(_bytes_data) <= MINT_SIZE or len(_bytes_data) <= ACCOUNT_SIZE or
                    len(_bytes_data) == MULTISIG_SIZE or _bytes_data[ACCOUNT_SIZE] != 1):
                self.fee_config_dict[address] = None
                return None

            _bytes_data = _bytes_data[ACCOUNT_SIZE + ACCOUNT_TYPE_SIZE:]

            index, EXTENSION, TYPE_SIZE, LENGTH_SIZE = 0, 1, 2, 2
            while index + TYPE_SIZE + LENGTH_SIZE <= len(_bytes_data):
                entry_type = int.from_bytes(_bytes_data[index:index + TYPE_SIZE], 'little')
                entry_length = int.from_bytes(_bytes_data[index + TYPE_SIZE:index + TYPE_SIZE + LENGTH_SIZE], 'little')
                type_index = index + TYPE_SIZE + LENGTH_SIZE
                if entry_type == EXTENSION:
                    return _bytes_data[type_index:type_index + entry_length]
                index = type_index + entry_length

            return None

        account_info = None
        try:
            account_info = await self.client.get_account_info(address)
        except Exception as e:
            self.logger.debug(f'Error fetching get_account_info by account {address}, {e}')

        if account_info is None or account_info.value is None or account_info.value.owner != TOKEN_2022_PROGRAM_ID:
            self.fee_config_dict[address] = None
            return None

        value = account_info.value

        tvl_data = _extract_extension_data(list(value.data))

        if tvl_data is not None:
            parsed_layout = FEE_CONFIG_LAYOUT.parse(bytes(tvl_data))
            fee_config = FeeConfig()
            fee_config.transfer_fee_config_authority = Pubkey.from_bytes(parsed_layout.transferFeeConfigAuthority)
            fee_config.withdraw_withheld_authority = Pubkey.from_bytes(parsed_layout.withdrawWithheldAuthority)
            fee_config.withheld_amount = parsed_layout.withheldAmount

            older_transfer_fee = TransferFee()
            older_transfer_fee.epoch = parsed_layout.olderTransferFee.epoch
            older_transfer_fee.maximum_fee = parsed_layout.olderTransferFee.maximumFee
            older_transfer_fee.transfer_fee_basis_points = parsed_layout.olderTransferFee.transferFeeBasisPoints

            newer_transfer_fee = TransferFee()
            newer_transfer_fee.epoch = parsed_layout.newerTransferFee.epoch
            newer_transfer_fee.maximum_fee = parsed_layout.newerTransferFee.maximumFee
            newer_transfer_fee.transfer_fee_basis_points = parsed_layout.newerTransferFee.transferFeeBasisPoints

            fee_config.older_transfer_fee = older_transfer_fee
            fee_config.newer_transfer_fee = newer_transfer_fee
            self.fee_config_dict[address] = fee_config
            return fee_config

        self.fee_config_dict[address] = None
        return None


