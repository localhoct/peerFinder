from scraper import safe_get
from parser import extract_peers, extract_subnets
import os
import re

URL = 'https://bgp.he.net/AS13335#_peers'
OUT = 'output'


def clean(name):
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name)


def get_peer_subnets(asn):
    url = f'https://bgp.he.net/{asn}'
    print('Fetching:', url)
    html = safe_get(url).text
    return extract_subnets(html)


def save_file(peer, subnets):
    folder = os.path.join(OUT, 'UNKNOWN')
    os.makedirs(folder, exist_ok=True)

    filename = clean(peer['name'] + '_' + peer['asn']) + '.txt'
    path = os.path.join(folder, filename)

    with open(path, 'w', encoding='utf-8') as f:
        for subnet in subnets:
            f.write(subnet + '\n')

    print('Saved:', path, 'subnets:', len(subnets))


def main():
    print('Fetching Cloudflare peers...')

    html = safe_get(URL).text
    peers = extract_peers(html)

    print('Peers found:', len(peers))

    os.makedirs(OUT, exist_ok=True)

    for peer in peers:
        subnets = get_peer_subnets(peer['asn'])
        if subnets:
            save_file(peer, subnets)
        else:
            print('No prefixes:', peer['asn'])


if __name__ == '__main__':
    main()
