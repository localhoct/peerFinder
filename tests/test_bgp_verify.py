import unittest

from bgp_verify import _asns_in, normalize_asn, validate_prefixes


class BgpVerifyTests(unittest.TestCase):
    def test_normalize_asn(self):
        self.assertEqual(normalize_asn("AS13335"), "AS13335")
        self.assertEqual(normalize_asn(13335), "AS13335")
        self.assertIsNone(normalize_asn("not-an-asn"))

    def test_extract_observed_neighbours_from_nested_data(self):
        value = {"v4": {"neighbours": [13335, "AS64500"]}, "v6": [64501]}
        self.assertEqual(_asns_in(value), {"AS13335", "AS64500", "AS64501"})

    def test_zero_limit_does_not_make_network_requests(self):
        result = validate_prefixes("AS13335", ["192.0.2.0/24"], limit=0)
        self.assertEqual(result, {"checked": 0, "states": {}, "prefixes": []})


if __name__ == "__main__":
    unittest.main()

