from typing import Union, Dict, Sequence

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.rpc.responses import GetAccountInfoResp

from construct import Bytes, Int16ul, Int64ul
from construct import Struct

from consts import TOKEN_2022_PROGRAM_ID
from data_types.fee_config import FeeConfig, TransferFee

PubkeyOrStr = Union[Pubkey, str]

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
        self.account_info_cache_manager = self.AccountInfoCacheManager()
        self.fee_config_cache_manager = self.FeeConfigCacheManager()

    async def get_account_info(self, address: PubkeyOrStr, encoding: str = 'jsonParsed'):
        if isinstance(address, str):
            address = Pubkey.from_string(address)

        if self.account_info_cache_manager.contains(address):
            return self.account_info_cache_manager.read(address)

        try:
            acc_info_resp = await self.client.get_account_info(address, encoding=encoding)
            if acc_info_resp.value is not None:
                self.account_info_cache_manager.write(address, acc_info_resp)
                return acc_info_resp
        except Exception:
            return None

    class AccountInfoCacheManager:
        def __init__(self):
            self.cache_dict: Dict[PubkeyOrStr, GetAccountInfoResp] = {}

        def write(self, key: PubkeyOrStr, value: GetAccountInfoResp):
            if key in self.cache_dict:
                raise KeyError(f"Try to write duplicate key {key} to AccountInfoCacheManager")
            self.cache_dict[key] = value

        def contains(self, key: PubkeyOrStr) -> bool:
            return key in self.cache_dict.keys()

        def read(self, key: PubkeyOrStr) -> GetAccountInfoResp:
            try:
                return self.cache_dict[key]
            except KeyError:
                raise KeyError(f"Record with key {key} is not found in AccountInfoCacheManager")

        def delete(self, keys: Union[PubkeyOrStr, Sequence[PubkeyOrStr]]):
            if isinstance(keys, PubkeyOrStr):
                keys = [keys]

            for key in keys:
                try:
                    del self.cache_dict[key]
                except KeyError:
                    raise KeyError(f"Record with key {key} is not found in AccountInfoCacheManager")

        def clear(self):
            self.cache_dict.clear()

        def size(self) -> int:
            return len(self.cache_dict)

    async def get_fee_config(self, address: PubkeyOrStr):
        # TODO: testcase 2b1kV6DkPAnxd5ixfnxCpjxmKwqjjaYmCZfHsFu24GXo
        # tx id 2nRKszNNFYHjKevkBs9zT7gctuCS7iFVQXPfuRKX5cfCeYAQwFsZP4N6GbkXvAJSnXjMk1aNhFyYtrtDimkhJBAD

        if self.fee_config_cache_manager.contains(address):
            return self.fee_config_cache_manager.read(address)

        def _extract_extension_data(_bytes_data: list[int]):
            # copy from "@solana/spl-token" ts package
            MINT_SIZE, ACCOUNT_SIZE, MULTISIG_SIZE, ACCOUNT_TYPE_SIZE = 82, 165, 355, 1

            if (len(_bytes_data) <= MINT_SIZE or len(_bytes_data) <= ACCOUNT_SIZE or
                    len(_bytes_data) == MULTISIG_SIZE or _bytes_data[ACCOUNT_SIZE] != 1):
                self.fee_config_cache_manager.write(address, None)
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

        account_info = await self.get_account_info(address, 'base64')
        value = account_info.value
        if value is None or value.owner != TOKEN_2022_PROGRAM_ID:
            self.fee_config_cache_manager.write(address, None)
            return None

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
            self.fee_config_cache_manager.write(address, fee_config)
            return fee_config

        self.fee_config_cache_manager.write(address, None)
        return None

    class FeeConfigCacheManager:
        def __init__(self):
            self.cache_dict: Dict[PubkeyOrStr, Union[FeeConfig, None]] = {}

        def write(self, key: PubkeyOrStr, value: Union[FeeConfig, None]):
            if key in self.cache_dict:
                raise KeyError(f"Try to write duplicate key {key} to FeeConfigCacheManager")
            self.cache_dict[key] = value

        def contains(self, key: PubkeyOrStr) -> bool:
            return key in self.cache_dict.keys()

        def read(self, key: PubkeyOrStr) -> Union[FeeConfig, None]:
            try:
                return self.cache_dict[key]
            except KeyError:
                raise KeyError(f"Record with key {key} is not found in FeeConfigCacheManager")

        def delete(self, keys: Union[PubkeyOrStr, Sequence[PubkeyOrStr]]):
            if isinstance(keys, PubkeyOrStr):
                keys = [keys]

            for key in keys:
                try:
                    del self.cache_dict[key]
                except KeyError:
                    raise KeyError(f"Record with key {key} is not found in FeeConfigCacheManager")

        def clear(self):
            self.cache_dict.clear()

        def size(self) -> int:
            return len(self.cache_dict)


