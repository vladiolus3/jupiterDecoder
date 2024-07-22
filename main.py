import asyncio

from solders.rpc.responses import GetTransactionResp
from solana.rpc.async_api import AsyncClient

from jup_rpc_client import JupRpcClient

clientAsync = AsyncClient('https://api.mainnet-beta.solana.com')


async def lookup_tx(tx_resp: GetTransactionResp):
    tx = tx_resp.value.transaction
    if tx.meta.err:
        print('Failed transaction {0}'.format(tx.meta.err))


if __name__ == '__main__':
    async def aaa():
        client = JupRpcClient('https://mainnet.helius-rpc.com/?api-key=8d81201e-5fa8-409c-bbf7-0f5bf70afbb7')
        tx = await client.decode_transaction('5zFrPZ7Hs8uLPEJFuHm16JDEyZuKgB3CSzrU1X3pTpXigfj1Kywht7Yhbqm15HqT9ZEtJn9zGooHGwLyCNCkTUbb')

        pass

    asyncio.run(aaa())
