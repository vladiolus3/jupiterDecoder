import abc
from typing import Dict

import aiohttp
import logger
from errors import EndpointError


class BaseSession(metaclass=abc.ABCMeta):
    def __init__(
            self,
            base_url: str = 'https://localhost',
    ):
        self._base_url = base_url
        connector = aiohttp.TCPConnector(
            ttl_dns_cache=60,
            enable_cleanup_closed=True
        )
        self._session = aiohttp.ClientSession(
            base_url=base_url,
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=60)
        )
        self._logger = logger.get_logger(__name__, filename=f'{__name__}.log')

    def __del__(self):
        self._session.connector.close()


class TokensJupSession(BaseSession):
    def __init__(self):
        # https://www.jupresear.ch/t/ecosystem-master-token-list/19786
        self._token_info_dict: Dict[str, any] = {}
        super().__init__('https://tokens.jup.ag')

    async def get_token_info(self, token_id: str):
        if token_id in self._token_info_dict.keys():
            return self._token_info_dict[token_id]

        url = '/token/{0}'.format(token_id)
        try:
            resp = await self._session.get(url)
            resp_json = await resp.json()
            self._token_info_dict[token_id] = resp_json
        except Exception as e:
            self._logger.error(
                f'Failed to fetch request from endpoint {self._base_url + url}, {e}',
                exc_info=True,
            )
            raise EndpointError(f'Failed to fetch request from endpoint {self._base_url + url}, {e}')

        return resp_json


