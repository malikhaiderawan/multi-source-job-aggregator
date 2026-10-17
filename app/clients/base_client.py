import httpx
import logging

logger = logging.getLogger("JobIntegrationGateway")

DEFAULT_TIMEOUT = 12.0
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 (JobDiscoveryGateway/2.0)",
    "Accept": "application/json, application/xml, text/xml;q=0.9, */*;q=0.8",
}

def create_async_client() -> httpx.AsyncClient:
    """Returns a pre-configured AsyncClient with sane timeouts and standard headers."""
    return httpx.AsyncClient(
        timeout=DEFAULT_TIMEOUT,
        headers=DEFAULT_HEADERS,
        follow_redirects=True
    )
