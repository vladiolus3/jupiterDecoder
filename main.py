import asyncio

from jup_rpc_client import JupRpcClient

if __name__ == '__main__':
    async def aaa():
        client = JupRpcClient('https://mainnet.helius-rpc.com/?api-key=8d81201e-5fa8-409c-bbf7-0f5bf70afbb7')
        tx = await client.decode_transaction('3b6xEqa7cZv8Gbo1VjaKKuLbbXDD4g9x1m5yzGgRfSb2ozktqCrY9BtoqkSiBgnu1uwMsjBWcqqHTE2eQDy9DtTR')

        pass

    asyncio.run(aaa())
