import asyncio
import os

from solders.pubkey import Pubkey

from src.http.jup_rpc_client import JupRpcClient
from src.logger import setup_logging

from dotenv import load_dotenv

load_dotenv()

if __name__ == '__main__':
    async def main():

        SOLANA_RPC_URL = os.getenv('SOLANA_RPC_URL')
        ITEMS_PER_SEC = int(os.getenv('ITEMS_PER_SEC'))
        setup_logging(os.getenv('LOGGER_LEVEL'))

        client = JupRpcClient(SOLANA_RPC_URL)
        txs = await client.client.get_signatures_for_address(
            Pubkey.from_string('BW6RXbEyug92G3DU8uMzP1SXynCCQMBGBy2tLFp8LbzU'), limit=100)
        tx_ids = [str(tx.signature) for tx in txs.value]

        for tx_id in tx_ids:
            print('tx_id: {0}'.format(tx_id))
            decoded_tx = await client.decode_transaction(tx_id)
            print('json: {0}\n'.format(decoded_tx[0] if len(decoded_tx) > 0 else []))

    asyncio.run(main())
