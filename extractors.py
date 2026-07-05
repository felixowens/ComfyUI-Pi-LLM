from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractionResult:
    text: str
    found: bool


def extract_text(
    text: str,
    extraction_mode: str,
    xml_tag: str,
    fence_language: str,
    start_delimiter: str,
    end_delimiter: str,
    occurrence: str,
    strip_whitespace: bool,
    fail_if_missing: bool,
) -> ExtractionResult:
    extracted = None

    if extraction_mode in ("auto", "xml_tag"):
        extracted = extract_xml_tag(text, xml_tag, occurrence)

    if extracted is None and extraction_mode in ("auto", "code_fence"):
        extracted = extract_code_fence(text, fence_language, occurrence)

    if extracted is None and extraction_mode in ("auto", "between_delimiters"):
        extracted = extract_between_delimiters(
            text, start_delimiter, end_delimiter, occurrence
        )

    found = extracted is not None
    if extracted is None:
        if fail_if_missing:
            raise ValueError(
                f"Pi Text Extractor could not find text using mode `{extraction_mode}`."
            )
        extracted = text

    if strip_whitespace:
        extracted = extracted.strip()

    return ExtractionResult(text=extracted, found=found)


def choose_match(matches: list[str], occurrence: str) -> str | None:
    if not matches:
        return None
    return matches[-1] if occurrence == "last" else matches[0]


def extract_xml_tag(text: str, xml_tag: str, occurrence: str) -> str | None:
    tag = xml_tag.strip()
    if not tag:
        return None
    tag_pattern = re.escape(tag)
    pattern = rf"<{tag_pattern}(?:\s[^>]*)?>(.*?)</{tag_pattern}>"
    matches = re.findall(pattern, text, flags=re.DOTALL | re.IGNORECASE)
    return choose_match(matches, occurrence)


def extract_code_fence(text: str, fence_language: str, occurrence: str) -> str | None:
    language = fence_language.strip()
    if language:
        pattern = rf"```[ \t]*{re.escape(language)}[^\n`]*\n(.*?)```"
    else:
        pattern = r"```[^\n`]*\n?(.*?)```"
    matches = re.findall(pattern, text, flags=re.DOTALL | re.IGNORECASE)
    return choose_match(matches, occurrence)


def extract_between_delimiters(
    text: str, start_delimiter: str, end_delimiter: str, occurrence: str
) -> str | None:
    start = start_delimiter.strip()
    end = end_delimiter.strip()
    if not start or not end:
        return None
    pattern = rf"{re.escape(start)}(.*?){re.escape(end)}"
    matches = re.findall(pattern, text, flags=re.DOTALL)
    return choose_match(matches, occurrence)
