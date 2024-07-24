import asyncio

from solders.rpc.responses import GetTransactionResp
from solana.rpc.async_api import AsyncClient

from account_info_manager import AccountInfoManager
from jup_rpc_client import JupRpcClient
from session import TokensJupSession

if __name__ == '__main__':
    async def aaa():
        tokens_jup_session = TokensJupSession()
        token_info = await tokens_jup_session.get_token_info('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v')
        print(token_info['name'])
        account_info_manager = AccountInfoManager('https://mainnet.helius-rpc.com/?api-key=8d81201e-5fa8-409c-bbf7-0f5bf70afbb7')
        client = JupRpcClient('https://mainnet.helius-rpc.com/?api-key=8d81201e-5fa8-409c-bbf7-0f5bf70afbb7')
        tx = await client.decode_transaction('3b6xEqa7cZv8Gbo1VjaKKuLbbXDD4g9x1m5yzGgRfSb2ozktqCrY9BtoqkSiBgnu1uwMsjBWcqqHTE2eQDy9DtTR')

        pass

    asyncio.run(aaa())
