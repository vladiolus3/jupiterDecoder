import asyncio
import logging
import os

from solders.pubkey import Pubkey

from src.http.account_info_manager import AccountInfoManager
from src.http.jup_rpc_client import JupRpcClient
from src.logger import setup_logging

from dotenv import load_dotenv

load_dotenv()

if __name__ == '__main__':
    async def main():

        SOLANA_RPC_URL = os.getenv('SOLANA_RPC_URL')
        setup_logging(os.getenv('LOGGER_LEVEL'))

        client = JupRpcClient(SOLANA_RPC_URL)
        account_info_manager = AccountInfoManager(SOLANA_RPC_URL)
        fee = await account_info_manager.get_fee_config('2b1kV6DkPAnxd5ixfnxCpjxmKwqjjaYmCZfHsFu24GXo')
        txs = await client.client.get_signatures_for_address(
            Pubkey.from_string('BW6RXbEyug92G3DU8uMzP1SXynCCQMBGBy2tLFp8LbzU'), limit=100)
        tx_ids = [str(tx.signature) for tx in txs.value]

        for tx_id in tx_ids:
            print('tx_id: {0}'.format(tx_id))
            decoded_tx = await client.decode_transaction(tx_id)
            logging.info('tx_id: {0}, decoded_tx: {1}'.format(
                tx_id, decoded_tx[0] if len(decoded_tx) > 0 else [])
            )

    asyncio.run(main())
