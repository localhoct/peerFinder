from bs4 import BeautifulSoup
import re


def extract_asns(html):
    soup = BeautifulSoup(html, 'html.parser')
    found = set()
    for text in soup.stripped_strings:
        for asn in re.findall(r'AS\d+', text):
            found.add(asn)
    return sorted(found)


def extract_subnets(html):
    return sorted(set(re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}/\d{1,2}\b', html)))
