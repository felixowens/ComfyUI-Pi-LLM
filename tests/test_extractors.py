from __future__ import annotations

import unittest

from extractors import extract_text


class ExtractorTests(unittest.TestCase):
    def test_extracts_xml_tag(self):
        result = extract_text(
            text="fluff <prompt> final prompt </prompt> end",
            extraction_mode="xml_tag",
            xml_tag="prompt",
            fence_language="",
            start_delimiter="",
            end_delimiter="",
            occurrence="first",
            strip_whitespace=True,
            fail_if_missing=False,
        )

        self.assertEqual(result.text, "final prompt")
        self.assertTrue(result.found)

    def test_extracts_last_code_fence_with_language(self):
        result = extract_text(
            text="```text\nfirst\n```\n```text\nsecond\n```",
            extraction_mode="code_fence",
            xml_tag="prompt",
            fence_language="text",
            start_delimiter="",
            end_delimiter="",
            occurrence="last",
            strip_whitespace=True,
            fail_if_missing=False,
        )

        self.assertEqual(result.text, "second")
        self.assertTrue(result.found)

    def test_extracts_between_custom_delimiters(self):
        result = extract_text(
            text="before [[PROMPT]]value[[/PROMPT]] after",
            extraction_mode="between_delimiters",
            xml_tag="prompt",
            fence_language="",
            start_delimiter="[[PROMPT]]",
            end_delimiter="[[/PROMPT]]",
            occurrence="first",
            strip_whitespace=True,
            fail_if_missing=False,
        )

        self.assertEqual(result.text, "value")
        self.assertTrue(result.found)

    def test_auto_falls_back_to_original_text_when_missing(self):
        result = extract_text(
            text="plain response",
            extraction_mode="auto",
            xml_tag="prompt",
            fence_language="",
            start_delimiter="",
            end_delimiter="",
            occurrence="first",
            strip_whitespace=True,
            fail_if_missing=False,
        )

        self.assertEqual(result.text, "plain response")
        self.assertFalse(result.found)

    def test_missing_wrapper_can_fail(self):
        with self.assertRaises(ValueError):
            extract_text(
                text="plain response",
                extraction_mode="xml_tag",
                xml_tag="prompt",
                fence_language="",
                start_delimiter="",
                end_delimiter="",
                occurrence="first",
                strip_whitespace=True,
                fail_if_missing=True,
            )


if __name__ == "__main__":
    unittest.main()
