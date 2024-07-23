from typing import Union, Sequence

from solders.transaction_status import ParsedInstruction, UiPartiallyDecodedInstruction, UiCompiledInstruction
from solders.transaction_status import EncodedTransactionWithStatusMeta

import base58

from anchorpy import EventCoder, InstructionCoder, Coder, NamedInstruction
from anchorpy_core.idl import Idl

from consts import (JUPITER_V6_PROGRAM_ID, TOKEN_PROGRAM_ID, TOKEN_2022_PROGRAM_ID,
                    TRANSFER_INSTRUCTION_TYPES, ROUTE_NAMES, AMM_TYPES,
                    MULTI_STEP_SWAPS, SWAP_IN_OUT_ACCOUNTS_POSITION,
                    SWAP_DIRECTION_ARGS)

from data_types.route_info import RouteInfo
from data_types.transfer_instructions import TransferInstructions
from data_types.swap import Swap

InnerInstruction = Union[ParsedInstruction, UiPartiallyDecodedInstruction, UiCompiledInstruction]
