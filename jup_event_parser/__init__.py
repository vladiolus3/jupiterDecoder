from typing import Union, Sequence

from solders.transaction_status import ParsedInstruction, UiPartiallyDecodedInstruction, UiCompiledInstruction
from solders.transaction_status import EncodedTransactionWithStatusMeta
from data_types.route_info import RouteInfo

import base58

from anchorpy import EventCoder, InstructionCoder, Coder, NamedInstruction
from anchorpy_core.idl import Idl

from consts import JUPITER_V6_PROGRAM_ID, ROUTE_NAMES, AMM_TYPES, MULTI_STEP_SWAPS, SWAP_IN_OUT_ACCOUNTS_POSITION, SWAP_DIRECTION_ARGS

from data_types.swap import *

import sumtypes

InnerInstruction = Union[ParsedInstruction, UiPartiallyDecodedInstruction, UiCompiledInstruction]
