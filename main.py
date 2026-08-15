from scraper import safe_get
from bs4 import BeautifulSoup
import os
import re

URL = 'https://bgp.he.net/AS13335#_peers'
OUT = 'output'


def clean(name):
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name)


def main():
    print('Fetching Cloudflare peers...')
    html = safe_get(URL).text
    soup = BeautifulSoup(html, 'lxml')
    print('Parser ready. Extend peer extraction here.')
    os.makedirs(OUT, exist_ok=True)


if __name__ == '__main__':
    main()
