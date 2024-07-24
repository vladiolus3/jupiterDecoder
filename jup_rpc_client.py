import time
from pathlib import Path
from typing import Union

from anchorpy_core.idl import Idl
from solana.rpc.async_api import AsyncClient
from solders.signature import Signature

from consts import JUPITER_V6_PROGRAM_ID
from jup_event_parser.jup_event_parser import JupEventParser

StrOrSignature = Union[str, Signature]

JUPITER_IDL_FILENAME = 'JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4.json'

if not (Path.cwd() / JUPITER_IDL_FILENAME).exists():
    raise FileNotFoundError(JUPITER_IDL_FILENAME)

file = open(JUPITER_IDL_FILENAME, 'r')
raw = file.read()
IDL = Idl.from_json(raw)


class JupRpcClient:
    def __init__(self, endpoint: str = 'https://api.mainnet-beta.solana.com'):
        self.client = AsyncClient(endpoint)
        self.jup_event_parser = JupEventParser(IDL, endpoint)
        self.download_secs = 0
        self.parse_secs = 0
        self.decode_count = 0
        self.not_parsed_count = 0

    async def decode_transaction(self, signature: StrOrSignature):
        if isinstance(signature, str):
            signature = Signature.from_string(signature)

        self.download_secs -= time.time()
        tx_resp = await self.client.get_transaction(
                        signature,
                        "jsonParsed",
                        max_supported_transaction_version=0,
                    )
        self.download_secs += time.time()

        tx = tx_resp.value.transaction
        if tx.meta.err:
            print('Failed transaction {0}'.format(tx.meta.err))

        self.parse_secs -= time.time()
        route_info_list = self.jup_event_parser.get_route_info_list(tx)
        swaps = []
        for route_info in route_info_list:
            swap = await self.jup_event_parser.extract_single_route(
                signature,
                tx,
                tx_resp.value.block_time,
                route_info,
                JUPITER_V6_PROGRAM_ID)
            if swap:
                swaps.append(swap)

        self.parse_secs += time.time()
        if len(swaps) == 0:
            self.not_parsed_count += 1
        else:
            self.decode_count += 1
        return swaps





