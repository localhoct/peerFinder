from scraper import safe_get
from parser import extract_asns, extract_subnets
from bs4 import BeautifulSoup
import os
import re

URL = 'https://bgp.he.net/AS13335#_peers'
OUT = 'output'


def clean(name):
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name)


def save_file(country, peer, subnets):
    folder = os.path.join(OUT, country)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, clean(peer) + '.txt')
    with open(path, 'w') as f:
        for subnet in subnets:
            f.write(subnet + '\n')


def main():
    print('Fetching Cloudflare peers...')
    html = safe_get(URL).text
    peers = extract_asns(html)
    subnets = extract_subnets(html)
    print(f'Peers found: {len(peers)}')
    print(f'Subnets found: {len(subnets)}')
    os.makedirs(OUT, exist_ok=True)
    for peer in peers:
        save_file('UNKNOWN', peer, subnets)
        print('Saved:', peer)


if __name__ == '__main__':
    main()
