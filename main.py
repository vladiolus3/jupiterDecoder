import asyncio

from solders.pubkey import Pubkey

from jup_rpc_client import JupRpcClient


if __name__ == '__main__':
    async def aaa():
        client = JupRpcClient('https://mainnet.helius-rpc.com/?api-key=8d81201e-5fa8-409c-bbf7-0f5bf70afbb7')
        txs = await client.client.get_signatures_for_address(
            Pubkey.from_string('BW6RXbEyug92G3DU8uMzP1SXynCCQMBGBy2tLFp8LbzU'), limit=1000)
        # tx_id = '3b6xEqa7cZv8Gbo1VjaKKuLbbXDD4g9x1m5yzGgRfSb2ozktqCrY9BtoqkSiBgnu1uwMsjBWcqqHTE2eQDy9DtTR'

        tx_id = '5P3bFgPhyiZDvpA7QPw5t1LNZjAmgwqALX5gnBcXo6PA5aY7FfGVnXWPqokjBTiNobegWgAvM31W3LwQFx47vrym'
        decoded_tx = await client.decode_transaction(tx_id)
        print(len(decoded_tx))

        tx_ids = [tx.signature for tx in txs.value]
        decoded_tx = None
        for i, tx_id in enumerate(tx_ids):
            print('{0}: {1}'.format(i, tx_id))
            decoded_tx = await client.decode_transaction(tx_id)
            print('\n')
        print(len(decoded_tx))
        print('time for downloading: {0},   time for decoding: {1}'.format(client.download_secs, client.decode_secs))
        print('decoded swaps count: {0},   not decoded swaps count: {1}'.format(client.decoded_swaps_count, client.not_decoded_swaps_count))
        pass
    asyncio.run(aaa())
