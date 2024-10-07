from .__init__ import *


class TransferInstructions:
    in_transfers: List[Union[ParsedInstruction, UiPartiallyDecodedInstruction, UiCompiledInstruction]] = []
    out_transfers: List[Union[ParsedInstruction, UiPartiallyDecodedInstruction, UiCompiledInstruction]] = []
