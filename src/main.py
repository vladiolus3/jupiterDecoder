import asyncio

from solders.pubkey import Pubkey

from src.http.jup_rpc_client import JupRpcClient
from src.logger import setup_logging

if __name__ == '__main__':
    async def aaa():
        setup_logging('debug')
        client = JupRpcClient()
        txs = await client.client.get_signatures_for_address(
           Pubkey.from_string('BW6RXbEyug92G3DU8uMzP1SXynCCQMBGBy2tLFp8LbzU'), limit=100)
        tx_ids = [str(tx.signature) for tx in txs.value]
        tx_id = '7mnSjET1QwKEmPe2bKdvrmFsv3J7Xf3bnEqEBg91X4JPUixfy5smRy75vu5iYF5x7nneUz7Wq4d1yjCewTanMyj'
        decoded_tx = await client.decode_transaction(tx_id)
        print('json: {0}\n'.format(decoded_tx[0].to_json() if len(decoded_tx) > 0 else []))

        for tx_id in tx_ids:
            print('tx_id: {0}'.format(tx_id))
            decoded_tx = await client.decode_transaction(tx_id)
            print('json: {0}\n'.format(decoded_tx[0].to_json() if len(decoded_tx) > 0 else []))

        print('download secs: {0} parse secs: {1}'.format(client.download_secs, client.parse_secs))
        print('decoded count: {0} not parsed count: {1}'.format(client.decode_count, client.not_parsed_count))
        print()

    asyncio.run(aaa())
