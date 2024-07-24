class SolanaTransactionFetchError(Exception):
    """Error while fetching solana transaction"""
    pass


class EndpointError(Exception):
    """Error while aiohttp_session initialization"""
    pass
