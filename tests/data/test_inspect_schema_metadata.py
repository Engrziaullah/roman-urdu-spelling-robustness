import unittest
from unittest.mock import patch

import src.data.inspect_schema as schema


class HubMetadataTests(unittest.TestCase):

    def fake_response(self, url, timeout=15):
        responses = {
            schema.INFO_URL: '{"sha": "test-sha", "cardData": {"license": "cc-by-4.0"}}',
            schema.SPLITS_URL: '{"splits": [{"config": "default", "split": "train"}]}',
            schema.SIZE_URL: '{"size": {"splits": [{"config": "default", "split": "train", "num_rows": 100}]}}',
            schema.CARD_URL: "# License\nlicense: cc-by-4.0",
        }
        if url not in responses:
            raise AssertionError(f"Unexpected URL: {url}")
        return responses[url]

    @patch("src.data.inspect_schema.fetch_text")
    def test_both_apis_success(self, mock_fetch):
        mock_fetch.side_effect = self.fake_response

        revision, splits, license_text = schema.get_hub_metadata()

        self.assertEqual(revision, "test-sha")
        self.assertIn("train (100 rows", splits)
        self.assertIn("cc-by-4.0", license_text)

    @patch("src.data.inspect_schema.fetch_text")
    def test_splits_api_fails_size_succeeds(self, mock_fetch):
        def response(url, timeout=15):
            if url == schema.SPLITS_URL:
                raise OSError("Splits unavailable")
            return self.fake_response(url, timeout)

        mock_fetch.side_effect = response

        _, splits, _ = schema.get_hub_metadata()

        self.assertIn("train (100 rows", splits)
        self.assertIn("Splits API detail", splits)

    @patch("src.data.inspect_schema.fetch_text")
    def test_size_api_fails_splits_succeeds(self, mock_fetch):
        def response(url, timeout=15):
            if url == schema.SIZE_URL:
                raise OSError("Size unavailable")
            return self.fake_response(url, timeout)

        mock_fetch.side_effect = response

        _, splits, _ = schema.get_hub_metadata()

        self.assertIn("train (unknown rows", splits)
        self.assertIn("Size API detail", splits)

    @patch("src.data.inspect_schema.fetch_text")
    def test_both_apis_fail(self, mock_fetch):
        def response(url, timeout=15):
            if url in (schema.SPLITS_URL, schema.SIZE_URL):
                raise OSError("API unavailable")
            return self.fake_response(url, timeout)

        mock_fetch.side_effect = response

        _, splits, _ = schema.get_hub_metadata()

        self.assertIn("No split entries", splits)
        self.assertIn("Splits API detail", splits)
        self.assertIn("Size API detail", splits)


if __name__ == "__main__":
    unittest.main()
