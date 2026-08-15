from scraper import safe_get
from parser import extract_peers, extract_subnets
import os
import re

URL = 'https://bgp.he.net/AS13335#_peers'
OUT = 'output'


def clean(name):
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name)


def save_file(peer, subnets):
    country = 'UNKNOWN'
    folder = os.path.join(OUT, country)
    os.makedirs(folder, exist_ok=True)

    filename = clean(peer['name'] + '_' + peer['asn']) + '.txt'
    path = os.path.join(folder, filename)

    with open(path, 'w', encoding='utf-8') as f:
        for subnet in subnets:
            f.write(subnet + '\n')

    print('Saved:', path)


def main():
    print('Fetching Cloudflare peers...')

    html = safe_get(URL).text

    peers = extract_peers(html)
    subnets = extract_subnets(html)

    print('Peers found:', len(peers))
    print('Subnets found:', len(subnets))

    for peer in peers:
        save_file(peer, subnets)


if __name__ == '__main__':
    main()
