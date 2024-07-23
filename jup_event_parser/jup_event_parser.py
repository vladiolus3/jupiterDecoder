from account_info_manager import AccountInfoManager
from consts import PLATFORM_FEE_ACCOUNTS_POSITION
from data_types.parsed_fee_event import ParsedFeeEvent
from data_types.parsed_swap_event import ParsedSwapEvent
from .__init__ import *
from .static_methods import _get_inner_instructions, _get_swaps, _get_in_and_out_transfer_instructions, \
    _is_fee_instruction


class JupEventParser(Coder):
    def __init__(self, idl: Idl, endpoint: str = 'https://api.mainnet-beta.solana.com'):
        self.account_info_manager = AccountInfoManager(endpoint)
        super().__init__(idl)

    def get_route_info_list(self, transaction_with_meta: EncodedTransactionWithStatusMeta):
        route_info_list = []
        for index, instruction in enumerate(transaction_with_meta.transaction.message.instructions):
            if instruction.program_id == JUPITER_V6_PROGRAM_ID:
                ix: NamedInstruction = self.instruction.parse(base58.b58decode(instruction.data))
                if ix.name in ROUTE_NAMES:
                    route_info_list.append(RouteInfo(
                        index,
                        1,
                        ix.name,
                        instruction.accounts,
                        ix.data
                    ))

        return route_info_list

    async def extract_single_route(self,
                                   transaction_with_meta: EncodedTransactionWithStatusMeta,
                                   route_info: RouteInfo):
        account_infos_map = []
        parsed_events = await self.get_parsed_events(transaction_with_meta, route_info)
        pass

    async def get_parsed_events(self,
                                transaction_with_meta: EncodedTransactionWithStatusMeta,
                                route_info: RouteInfo):
        events = []
        inner_instructions = _get_inner_instructions(transaction_with_meta, route_info)
        swaps = _get_swaps(inner_instructions, route_info)
        for swap in swaps:
            transfer_instructions = _get_in_and_out_transfer_instructions(inner_instructions, swap)
            in_transfer_data = await self.get_transfer_data(transfer_instructions.in_transfers, 'in')
            out_transfer_data = await self.get_transfer_data(transfer_instructions.out_transfers, 'out')
            swap_event = ParsedEvent()
            swap_event.name = 'ParsedSwapEvent'
            swap_event.data = ParsedSwapEvent()
            swap_event.data.amm = inner_instructions[swap.instruction_index].program_id
            swap_event.data.input_mint = in_transfer_data['mint']
            swap_event.data.input_amount = in_transfer_data['amount']
            swap_event.data.output_mint = out_transfer_data['mint']
            swap_event.data.output_amount = out_transfer_data['amount']
            events.append(swap_event)

        if route_info.data.platform_fee_bps > 0:
            swap_fee = await self.get_swap_fee(route_info, inner_instructions)
            if swap_fee is None:
                return events

            fee_event = ParsedEvent()
            fee_event.name = 'ParsedFeeEvent'
            fee_event.data = ParsedFeeEvent()
            fee_event.data.account = Pubkey.from_string(swap_fee['account'])
            fee_event.data.mint = Pubkey.from_string(swap_fee['mint'])
            fee_event.data.amount = swap_fee['amount']
            events.append(fee_event)

        return events

    async def get_transfer_data(self, transfer_instructions: Sequence[InnerInstruction], transfer_type: str):
        mint = ''
        amount = 0
        for instruction in transfer_instructions:
            if (instruction.parsed['type'] == 'transferChecked' or
                    instruction.parsed['type'] == 'transferCheckedWithFee'):
                if transfer_type == 'out':
                    amount = (amount + await self.get_exact_out_amount_after_fee(
                        instruction.parsed['info'],
                        instruction.parsed['type']))
                else:
                    amount = amount + int(instruction.parsed['info']['tokenAmount']['amount'])
            else:
                amount = amount + int(instruction.parsed['info']['amount'])

        transfer_instruction = transfer_instructions[0]
        if transfer_instruction.parsed['type'] == 'transfer':
            if transfer_type == 'in':
                account = transfer_instruction.parsed['info']['destination']
            else:
                account = transfer_instruction.parsed['info']['source']

            account_info = await self.account_info_manager.get_account_info_json_parsed(account)
            if account_info is None:
                mint = transfer_instruction.parsed['info']['mint']
            else:
                mint = account_info.value.data.parsed['info']['mint']
        else:
            mint = transfer_instruction.parsed['info']['mint']

        return {'mint': mint, 'amount': amount}

    async def get_exact_out_amount_after_fee(self, info: dict, _type: str):
        # testcase 2b1kV6DkPAnxd5ixfnxCpjxmKwqjjaYmCZfHsFu24GXo
        # tx_id 2nRKszNNFYHjKevkBs9zT7gctuCS7iFVQXPfuRKX5cfCeYAQwFsZP4N6GbkXvAJSnXjMk1aNhFyYtrtDimkhJBAD

        if _type == 'transferChecked':
            fee_config = await self.account_info_manager.get_fee_config(info['mint'])
            if fee_config is None:
                return int(info['tokenAmount']['amount'])

            fee_basis_points = fee_config.newer_transfer_fee.transfer_fee_basis_points
            amount = int(info['tokenAmount']['amount'])
            fee = amount * fee_basis_points / 10_000
            return amount - fee

        return int(info['tokenAmount']['amount']) - int(info['feeAmount']['amount'])

    async def get_swap_fee(self, route_info: RouteInfo, inner_instructions: Sequence[InnerInstruction]):
        position = PLATFORM_FEE_ACCOUNTS_POSITION[route_info.name]
        fee_account = route_info.accounts[position]  # base58 ???

        for inner_instruction in inner_instructions:
            if not hasattr(inner_instruction, 'parsed') or inner_instruction.parsed is None:
                continue

            destination = inner_instruction.parsed['info']['destination']
            if _is_fee_instruction(inner_instruction, str(fee_account),
                                   destination, route_info.stack_height):
                if inner_instruction.parsed['type'] == 'transfer':
                    account_info = await self.account_info_manager.get_account_info_json_parsed(destination)
                    mint = account_info.value.data.parsed['info']['mint']
                else:
                    mint = inner_instruction.parsed['info']['mint']

                if inner_instruction.parsed['type'] == 'transferChecked':
                    amount = inner_instruction.parsed['info']['tokenAmount']['amount']
                else:
                    amount = inner_instruction.parsed['info']['amount']

                return {'mint': mint, 'amount': amount, 'account': destination}

        return None
