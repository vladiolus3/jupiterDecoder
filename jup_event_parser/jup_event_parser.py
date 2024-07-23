from .__init__ import *
from .static_methods import _get_inner_instructions, _get_swaps, _get_in_and_out_transfer_instructions


class JupEventParser(Coder):
    def __init__(self, idl: Idl):
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

    def extract_single_route(self,
                             transaction_with_meta: EncodedTransactionWithStatusMeta,
                             route_info: RouteInfo):
        account_infos_map = []
        parsed_events = self.get_parsed_events(transaction_with_meta, route_info)
        pass

    def get_parsed_events(self,
                          transaction_with_meta: EncodedTransactionWithStatusMeta,
                          route_info: RouteInfo):
        events = []
        inner_instructions = _get_inner_instructions(transaction_with_meta, route_info)
        swaps = _get_swaps(inner_instructions, route_info)
        for swap in swaps:
            transfer_instructions = _get_in_and_out_transfer_instructions(inner_instructions, swap)

    def get_transfer_data(self, transfer_instructions: Sequence[InnerInstruction], transfer_type: str):
        mint = ''
        amount = 0
        for instruction in transfer_instructions:
            if (instruction.parsed['type'] == 'transferChecked' or
                    instruction.parsed['type'] == 'transferCheckedWithFee'):
                if transfer_type == 'out':
                    pass

    def get_exact_out_amount_after_fee(self, info: dict, transfer_instruction_type: str, _type: str):
        # https://solscan.io/tx/2nRKszNNFYHjKevkBs9zT7gctuCS7iFVQXPfuRKX5cfCeYAQwFsZP4N6GbkXvAJSnXjMk1aNhFyYtrtDimkhJBAD
        if transfer_instruction_type == 'transferChecked':
            try:
                pass
            except:
                pass

