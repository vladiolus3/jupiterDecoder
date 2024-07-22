from .__init__ import *


class ParsedSwapEvent:
    amm: Pubkey
    input_mint: Pubkey
    input_amount: int
    output_mint: Pubkey
    output_amount: int
