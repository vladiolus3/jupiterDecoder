from .parsed_swap_event import *
from .parsed_fee_event import *


class ParsedEvent:
    data: Union[ParsedSwapEvent, ParsedFeeEvent]
    name: str
