from .__init__ import *


class RouteInfo:
    def __init__(self,
                 index: int,
                 stack_height: int,
                 name: str,
                 accounts: List[Pubkey],
                 data: Container):
        self.index = index
        self.stack_height = stack_height
        self.name = name
        self.accounts = accounts
        self.data = data
