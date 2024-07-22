from .__init__ import *
from .static_methods import _get_inner_instructions, _get_swaps


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
            pass


