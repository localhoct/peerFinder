"""HTTP helpers with retries, persistent caching, and thread-local sessions."""

import random
import threading
import time

import requests_cache
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


_LOCAL = threading.local()
_CACHE_NAME = "cache/bgp_cache"
_HEADERS = {"User-Agent": "PeerFinder/2.0 (+https://github.com/localhoct/peerFinder)"}


def _session():
    """Return one cached HTTP session per worker thread.

    A requests session is not shared between workers. The filesystem backend
    avoids SQLite write contention while several peer pages are fetched at once.
    """
    if not hasattr(_LOCAL, "session"):
        retry = Retry(
            total=4,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(("GET",)),
            respect_retry_after_header=True,
        )
        session = requests_cache.CachedSession(
            cache_name=_CACHE_NAME,
            backend="filesystem",
            expire_after=86400,
            allowable_methods=("GET",),
        )
        session.headers.update(_HEADERS)
        session.mount("https://", HTTPAdapter(max_retries=retry, pool_connections=16, pool_maxsize=16))
        _LOCAL.session = session
    return _LOCAL.session


def safe_get(url, *, params=None, timeout=30, delay=(0.15, 0.4)):
    """Fetch a URL safely, with an optional small polite delay before a cache miss."""
    session = _session()
    response = session.get(url, params=params, timeout=timeout)
    if not getattr(response, "from_cache", False) and delay:
        # The delay is intentionally paid after the request: it spaces a worker's
        # requests without making cache hits or unrelated workers wait.
        time.sleep(random.uniform(*delay))
    response.raise_for_status()
    return response

