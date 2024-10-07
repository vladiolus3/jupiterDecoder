import datetime
from typing import Union, Sequence, List
from decimal import Decimal, getcontext, ROUND_HALF_UP

from solders.transaction_status import ParsedInstruction, UiPartiallyDecodedInstruction, UiCompiledInstruction
from solders.transaction_status import EncodedTransactionWithStatusMeta
from solders.pubkey import Pubkey
from solders.signature import Signature

from anchorpy import EventCoder, InstructionCoder, Coder, NamedInstruction
from anchorpy_core.idl import Idl

from src.consts import (JUPITER_V6_PROGRAM_ID, TOKEN_PROGRAM_ID, TOKEN_2022_PROGRAM_ID,
                    TRANSFER_INSTRUCTION_TYPES, ROUTE_NAMES, AMM_TYPES,
                    MULTI_STEP_SWAPS, SWAP_IN_OUT_ACCOUNTS_POSITION,
                    SWAP_DIRECTION_ARGS, PLATFORM_FEE_ACCOUNTS_POSITION)

from src.contracts.route_info import RouteInfo
from src.contracts.transfer_instructions import TransferInstructions
from src.contracts.swap import Swap
from src.contracts.parsed_event import ParsedEvent
from src.contracts.parsed_fee_event import ParsedFeeEvent
from src.contracts.parsed_swap_event import ParsedSwapEvent
from src.contracts.swap_attributes import SwapAttributes

from src.http.session import TokensJupSession, PriceJupSession
from src.http.account_info_manager import AccountInfoManager

import asyncio
from typing import Dict

import base58
from solders.rpc.responses import GetAccountInfoMaybeJsonParsedResp as AccountInfo

InnerInstruction = Union[ParsedInstruction, UiPartiallyDecodedInstruction, UiCompiledInstruction]

# round decimal values
# getcontext().prec = 10
# getcontext().rounding = ROUND_HALF_UP
