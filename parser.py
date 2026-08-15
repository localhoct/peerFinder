from bs4 import BeautifulSoup
import re


def extract_peers(html):
    soup = BeautifulSoup(html, 'html.parser')
    peers = []

    for row in soup.find_all('tr'):
        cols = [c.get_text(' ', strip=True) for c in row.find_all('td')]
        if not cols:
            continue

        text = ' '.join(cols)
        match = re.search(r'AS(\d+)', text)
        if match:
            name = cols[1] if len(cols) > 1 else match.group(0)
            peers.append({
                'asn': 'AS' + match.group(1),
                'name': name
            })

    unique = {}
    for peer in peers:
        unique[peer['asn']] = peer

    return list(unique.values())


def extract_subnets(html):
    return sorted(set(
        re.findall(
            r'\b(?:\d{1,3}\.){3}\d{1,3}/\d{1,2}\b',
            html
        )
    ))
