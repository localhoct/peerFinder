import unittest

from parser import has_cloudflare_link


PEERS_TABLE = """
<table>
<tr><th>PEERS</th></tr>
<tr>
  <td><a href="/AS13335">AS13335</a></td>
  <td>Cloudflare, Inc.</td>
  <td>US</td>
</tr>
<tr>
  <td><a href="/AS20940">AS20940</a></td>
  <td>Akamai</td>
  <td>US</td>
</tr>
</table>
"""

DECOY_TABLE = """
<table>
<tr><th>PEERS</th></tr>
<tr>
  <td><a href="/AS133350">AS133350</a></td>
  <td>Not Cloudflare Corp</td>
  <td>JP</td>
</tr>
</table>
"""


class ParserTests(unittest.TestCase):
    def test_detects_direct_peer_immediately_followed_by_name_text(self):
        # Regression test: get_text(" ") only inserts a space *between* cells.
        # A previous implementation then stripped all spaces before running a
        # \b-bounded regex, which merged "AS13335" into the next cell's text
        # (e.g. "AS13335CLOUDFLARE...") and made \b fail to match at the join,
        # so a real direct peer was silently reported as not a peer.
        self.assertTrue(has_cloudflare_link(PEERS_TABLE, "AS13335"))

    def test_does_not_match_longer_asn_as_substring(self):
        # AS133350 must not be mistaken for AS13335.
        self.assertFalse(has_cloudflare_link(DECOY_TABLE, "AS13335"))

    def test_no_peers_table_returns_false(self):
        self.assertFalse(has_cloudflare_link("<table><tr><td>nothing</td></tr></table>", "AS13335"))


if __name__ == "__main__":
    unittest.main()
