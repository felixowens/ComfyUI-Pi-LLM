from __future__ import annotations

import os
import re
import subprocess
import time
from typing import ClassVar


class PiLLMText:
    """Run Pi in print mode and return its LLM response as a ComfyUI STRING."""

    CATEGORY = "Pi"
    FUNCTION = "generate"
    RETURN_TYPES: ClassVar[tuple[str, ...]] = ("STRING",)
    RETURN_NAMES: ClassVar[tuple[str, ...]] = ("text",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "system_instruction": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "You are a helpful assistant. Return only the requested text.",
                    },
                ),
                "model_name": (
                    [
                        "minimax/MiniMax-M3",
                        "minimax/MiniMax-M2.7",
                        "minimax/MiniMax-M2.7-highspeed",
                        "anthropic/claude-3-5-sonnet-20240620",
                        "anthropic/claude-3-5-sonnet-20241022",
                        "anthropic/claude-3-7-sonnet-20250219",
                        "anthropic/claude-3-haiku-20240307",
                        "anthropic/claude-3-opus-20240229",
                        "anthropic/claude-3-sonnet-20240229",
                        "anthropic/claude-fable-5",
                        "anthropic/claude-haiku-4-5",
                        "anthropic/claude-haiku-4-5-20251001",
                        "anthropic/claude-opus-4-0",
                        "anthropic/claude-opus-4-1",
                        "anthropic/claude-opus-4-1-20250805",
                        "anthropic/claude-opus-4-20250514",
                        "anthropic/claude-opus-4-5",
                        "anthropic/claude-opus-4-5-20251101",
                        "anthropic/claude-opus-4-6",
                        "anthropic/claude-opus-4-7",
                        "anthropic/claude-opus-4-8",
                        "anthropic/claude-sonnet-4-0",
                        "anthropic/claude-sonnet-4-20250514",
                        "anthropic/claude-sonnet-4-5",
                        "anthropic/claude-sonnet-4-5-20250929",
                        "anthropic/claude-sonnet-4-6",
                        "anthropic/claude-sonnet-5",
                        "openai-codex/gpt-5.3-codex-spark",
                        "openai-codex/gpt-5.4",
                        "openai-codex/gpt-5.4-mini",
                        "openai-codex/gpt-5.5",
                    ],
                    {"default": "minimax/MiniMax-M3"},
                ),
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "What should the LLM do or produce? Include any input text here.",
                    },
                ),
                "seed": (
                    "INT",
                    {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF, "step": 1},
                ),
                "timeout_seconds": (
                    "INT",
                    {"default": 120, "min": 1, "max": 3600, "step": 1},
                ),
                "run_every_queue": (
                    "BOOLEAN",
                    {"default": False},
                ),
            },
            "optional": {
                "connected_text": (
                    "STRING",
                    {
                        "multiline": True,
                        "placeholder": "Optional extra STRING input appended after prompt.",
                    },
                ),
            },
        }

    @classmethod
    def IS_CHANGED(
        cls,
        system_instruction: str,
        model_name: str,
        prompt: str,
        seed: int,
        timeout_seconds: int,
        run_every_queue: bool,
        connected_text: str = "",
    ):
        if run_every_queue:
            return time.time()
        return (
            system_instruction,
            model_name,
            prompt,
            seed,
            timeout_seconds,
            connected_text,
        )

    def generate(
        self,
        system_instruction: str,
        model_name: str,
        prompt: str,
        seed: int,
        timeout_seconds: int,
        run_every_queue: bool,
        connected_text: str = "",
    ):
        combined_prompt = self._build_prompt(prompt, connected_text)
        if not combined_prompt.strip():
            raise ValueError("Pi LLM Text requires a non-empty prompt or connected_text input.")

        command = self._build_command(system_instruction, model_name, combined_prompt)

        env = os.environ.copy()
        env.setdefault("NO_COLOR", "1")

        try:
            result = subprocess.run(
                command,
                shell=False,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(
                f"Pi timed out after {timeout_seconds} seconds while generating text."
            ) from exc
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                "Could not find the `pi` executable. Ensure Pi is installed and on the PATH "
                "visible to the ComfyUI process."
            ) from exc

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            detail = stderr or stdout or "No error output was produced."
            raise RuntimeError(f"Pi exited with code {result.returncode}:\n{detail}")

        return (stdout,)

    @staticmethod
    def _build_prompt(*parts: str) -> str:
        non_empty_parts = [part.strip() for part in parts if part and part.strip()]
        return "\n\n".join(non_empty_parts)

    @staticmethod
    def _build_command(system_instruction: str, model_name: str, prompt: str) -> list[str]:
        command = [
            "pi",
            "-p",
            "--no-tools",
            "--no-context-files",
            "--no-session",
            "--system-prompt",
            system_instruction,
        ]

        if model_name.strip():
            command.extend(["--model", model_name.strip()])

        command.append(prompt)
        return command


class PiTextExtractor:
    """Extract generated text from common LLM wrappers like XML tags or code fences."""

    CATEGORY = "Pi"
    FUNCTION = "extract"
    RETURN_TYPES: ClassVar[tuple[str, ...]] = ("STRING", "BOOLEAN")
    RETURN_NAMES: ClassVar[tuple[str, ...]] = ("text", "found")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "LLM response to extract from.",
                    },
                ),
                "extraction_mode": (
                    ["auto", "xml_tag", "code_fence", "between_delimiters"],
                    {"default": "auto"},
                ),
                "xml_tag": (
                    "STRING",
                    {
                        "multiline": False,
                        "default": "prompt",
                        "placeholder": "For <prompt>...</prompt> style extraction.",
                    },
                ),
                "fence_language": (
                    "STRING",
                    {
                        "multiline": False,
                        "default": "",
                        "placeholder": "Optional, e.g. text, markdown, json. Empty = any fence.",
                    },
                ),
                "start_delimiter": (
                    "STRING",
                    {
                        "multiline": False,
                        "default": "",
                        "placeholder": "Custom start marker, e.g. [[PROMPT]].",
                    },
                ),
                "end_delimiter": (
                    "STRING",
                    {
                        "multiline": False,
                        "default": "",
                        "placeholder": "Custom end marker, e.g. [[/PROMPT]].",
                    },
                ),
                "occurrence": (["first", "last"], {"default": "first"}),
                "strip_whitespace": ("BOOLEAN", {"default": True}),
                "fail_if_missing": ("BOOLEAN", {"default": False}),
            }
        }

    def extract(
        self,
        text: str,
        extraction_mode: str,
        xml_tag: str,
        fence_language: str,
        start_delimiter: str,
        end_delimiter: str,
        occurrence: str,
        strip_whitespace: bool,
        fail_if_missing: bool,
    ):
        extracted = None

        if extraction_mode in ("auto", "xml_tag"):
            extracted = self._extract_xml_tag(text, xml_tag, occurrence)

        if extracted is None and extraction_mode in ("auto", "code_fence"):
            extracted = self._extract_code_fence(text, fence_language, occurrence)

        if extracted is None and extraction_mode in ("auto", "between_delimiters"):
            extracted = self._extract_between_delimiters(
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

        return (extracted, found)

    @staticmethod
    def _choose_match(matches: list[str], occurrence: str) -> str | None:
        if not matches:
            return None
        return matches[-1] if occurrence == "last" else matches[0]

    @classmethod
    def _extract_xml_tag(cls, text: str, xml_tag: str, occurrence: str) -> str | None:
        tag = xml_tag.strip()
        if not tag:
            return None
        tag_pattern = re.escape(tag)
        pattern = rf"<{tag_pattern}(?:\s[^>]*)?>(.*?)</{tag_pattern}>"
        matches = re.findall(pattern, text, flags=re.DOTALL | re.IGNORECASE)
        return cls._choose_match(matches, occurrence)

    @classmethod
    def _extract_code_fence(
        cls, text: str, fence_language: str, occurrence: str
    ) -> str | None:
        language = fence_language.strip()
        if language:
            pattern = rf"```[ \t]*{re.escape(language)}[^\n`]*\n(.*?)```"
        else:
            pattern = r"```[^\n`]*\n?(.*?)```"
        matches = re.findall(pattern, text, flags=re.DOTALL | re.IGNORECASE)
        return cls._choose_match(matches, occurrence)

    @classmethod
    def _extract_between_delimiters(
        cls, text: str, start_delimiter: str, end_delimiter: str, occurrence: str
    ) -> str | None:
        start = start_delimiter.strip()
        end = end_delimiter.strip()
        if not start or not end:
            return None
        pattern = rf"{re.escape(start)}(.*?){re.escape(end)}"
        matches = re.findall(pattern, text, flags=re.DOTALL)
        return cls._choose_match(matches, occurrence)


NODE_CLASS_MAPPINGS = {
    "PiLLMText": PiLLMText,
    "PiTextExtractor": PiTextExtractor,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PiLLMText": "Pi LLM Text",
    "PiTextExtractor": "Pi Text Extractor",
}
