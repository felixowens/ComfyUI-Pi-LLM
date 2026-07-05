from __future__ import annotations

import time
from typing import ClassVar

try:
    from .extractors import extract_text
    from .models import AVAILABLE_MODELS, DEFAULT_MODEL
    from .pi_runner import (
        CACHE_MODES,
        DEFAULT_CACHE_MODE,
        DEFAULT_RESPONSE_MODE,
        RESPONSE_MODES,
        PiRequest,
        build_prompt,
        resolve_pi_response,
        should_use_saved_response,
    )
    from .wildcards import WildcardInputs, compose_wildcard_prompt
except ImportError:  # Allows direct local imports during simple test runs.
    from extractors import extract_text
    from models import AVAILABLE_MODELS, DEFAULT_MODEL
    from pi_runner import (
        CACHE_MODES,
        DEFAULT_CACHE_MODE,
        DEFAULT_RESPONSE_MODE,
        RESPONSE_MODES,
        PiRequest,
        build_prompt,
        resolve_pi_response,
        should_use_saved_response,
    )
    from wildcards import WildcardInputs, compose_wildcard_prompt


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
                "model_name": (AVAILABLE_MODELS, {"default": DEFAULT_MODEL}),
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "What should the LLM do or produce? Include any input text here.",
                    },
                ),
                "response_mode": (RESPONSE_MODES, {"default": DEFAULT_RESPONSE_MODE}),
                "cache_mode": (CACHE_MODES, {"default": DEFAULT_CACHE_MODE}),
                "saved_response": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "Paste a previous LLM output here for reproducible reruns. Default mode uses this when non-empty.",
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
                "run_every_queue": ("BOOLEAN", {"default": False}),
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
        response_mode: str,
        cache_mode: str,
        saved_response: str,
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
            response_mode,
            cache_mode,
            saved_response,
            seed,
            timeout_seconds,
            connected_text,
        )

    def generate(
        self,
        system_instruction: str,
        model_name: str,
        prompt: str,
        response_mode: str,
        cache_mode: str,
        saved_response: str,
        seed: int,
        timeout_seconds: int,
        run_every_queue: bool,
        connected_text: str = "",
    ):
        if should_use_saved_response(response_mode, saved_response):
            return (saved_response.strip(),)

        combined_prompt = build_prompt(prompt, connected_text)
        if not combined_prompt.strip():
            raise ValueError("Pi LLM Text requires a non-empty prompt or connected_text input.")

        response = resolve_pi_response(
            PiRequest(
                system_instruction=system_instruction,
                model_name=model_name,
                prompt=combined_prompt,
            ),
            seed=seed,
            timeout_seconds=timeout_seconds,
            cache_mode=cache_mode,
        )
        return (response,)


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
        result = extract_text(
            text=text,
            extraction_mode=extraction_mode,
            xml_tag=xml_tag,
            fence_language=fence_language,
            start_delimiter=start_delimiter,
            end_delimiter=end_delimiter,
            occurrence=occurrence,
            strip_whitespace=strip_whitespace,
            fail_if_missing=fail_if_missing,
        )
        return (result.text, result.found)


class PiWildcardPrompt:
    """Seeded prompt composer for randomly selecting wildcard fragments."""

    CATEGORY = "Pi"
    FUNCTION = "compose"
    RETURN_TYPES: ClassVar[tuple[str, ...]] = ("STRING", "STRING", "STRING")
    RETURN_NAMES: ClassVar[tuple[str, ...]] = (
        "positive_prompt",
        "negative_prompt",
        "selected",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt_template": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "Optional template, e.g. {base_prompt}, {characters}, wearing {clothing}, {styles}. Blank = append selected fragments.",
                    },
                ),
                "negative_template": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "Optional negative template, e.g. {base_negative}, {dislikes}. Blank = append selected dislikes.",
                    },
                ),
                "base_prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "Base positive text. Use {base_prompt} in prompt_template, or leave template blank to prepend it.",
                    },
                ),
                "base_negative": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "Always included at the start of the negative prompt.",
                    },
                ),
                "likes": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "One liked prompt fragment per line. # comments ignored.",
                    },
                ),
                "dislikes": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "One negative prompt fragment per line. # comments ignored.",
                    },
                ),
                "characters": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "One character/subject option per line.",
                    },
                ),
                "clothing": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "One clothing/accessory option per line.",
                    },
                ),
                "styles": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "One visual/style option per line.",
                    },
                ),
                "extra": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "Any other prompt fragments, one per line.",
                    },
                ),
                "seed": (
                    "INT",
                    {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF, "step": 1},
                ),
                "likes_count": ("INT", {"default": 1, "min": 0, "max": 64, "step": 1}),
                "dislikes_count": ("INT", {"default": 1, "min": 0, "max": 64, "step": 1}),
                "characters_count": ("INT", {"default": 1, "min": 0, "max": 64, "step": 1}),
                "clothing_count": ("INT", {"default": 1, "min": 0, "max": 64, "step": 1}),
                "styles_count": ("INT", {"default": 1, "min": 0, "max": 64, "step": 1}),
                "extra_count": ("INT", {"default": 1, "min": 0, "max": 64, "step": 1}),
                "separator": (["comma", "space", "newline"], {"default": "comma"}),
                "dedupe": ("BOOLEAN", {"default": True}),
                "shuffle_positive": ("BOOLEAN", {"default": False}),
            }
        }

    def compose(
        self,
        prompt_template: str,
        negative_template: str,
        base_prompt: str,
        base_negative: str,
        likes: str,
        dislikes: str,
        characters: str,
        clothing: str,
        styles: str,
        extra: str,
        seed: int,
        likes_count: int,
        dislikes_count: int,
        characters_count: int,
        clothing_count: int,
        styles_count: int,
        extra_count: int,
        separator: str,
        dedupe: bool,
        shuffle_positive: bool,
    ):
        result = compose_wildcard_prompt(
            WildcardInputs(
                prompt_template=prompt_template,
                negative_template=negative_template,
                base_prompt=base_prompt,
                base_negative=base_negative,
                likes=likes,
                dislikes=dislikes,
                characters=characters,
                clothing=clothing,
                styles=styles,
                extra=extra,
                seed=seed,
                likes_count=likes_count,
                dislikes_count=dislikes_count,
                characters_count=characters_count,
                clothing_count=clothing_count,
                styles_count=styles_count,
                extra_count=extra_count,
                separator=separator,
                dedupe=dedupe,
                shuffle_positive=shuffle_positive,
            )
        )
        return (result.positive_prompt, result.negative_prompt, result.selected)


NODE_CLASS_MAPPINGS = {
    "PiLLMText": PiLLMText,
    "PiTextExtractor": PiTextExtractor,
    "PiWildcardPrompt": PiWildcardPrompt,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PiLLMText": "Pi LLM Text",
    "PiTextExtractor": "Pi Text Extractor",
    "PiWildcardPrompt": "Pi Wildcard Prompt",
}
