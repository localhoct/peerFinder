import time
import random
import requests
import requests_cache
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

requests_cache.install_cache('cache/bgp_cache', expire_after=86400)

session = requests.Session()
retry = Retry(total=5, backoff_factor=2, status_forcelist=[429,500,502,503,504], allowed_methods=['GET'])
session.mount('https://', HTTPAdapter(max_retries=retry))

HEADERS = {'User-Agent': 'Mozilla/5.0 PeerFinder/1.0'}


def safe_get(url):
    time.sleep(random.uniform(2,6))
    r = session.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r
