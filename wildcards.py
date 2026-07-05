from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class WildcardInputs:
    base_prompt: str
    base_negative: str
    likes: str
    dislikes: str
    characters: str
    clothing: str
    styles: str
    extra: str
    seed: int
    likes_count: int
    dislikes_count: int
    characters_count: int
    clothing_count: int
    styles_count: int
    extra_count: int
    separator: str
    dedupe: bool
    shuffle_positive: bool


@dataclass(frozen=True)
class WildcardResult:
    positive_prompt: str
    negative_prompt: str
    selected: str


def compose_wildcard_prompt(inputs: WildcardInputs) -> WildcardResult:
    rng = random.Random(inputs.seed)

    selected_likes = sample_lines(rng, inputs.likes, inputs.likes_count)
    selected_dislikes = sample_lines(rng, inputs.dislikes, inputs.dislikes_count)
    selected_characters = sample_lines(rng, inputs.characters, inputs.characters_count)
    selected_clothing = sample_lines(rng, inputs.clothing, inputs.clothing_count)
    selected_styles = sample_lines(rng, inputs.styles, inputs.styles_count)
    selected_extra = sample_lines(rng, inputs.extra, inputs.extra_count)

    base_positive_parts = clean_base(inputs.base_prompt)
    positive_parts = (
        base_positive_parts
        + selected_likes
        + selected_characters
        + selected_clothing
        + selected_styles
        + selected_extra
    )
    negative_parts = clean_base(inputs.base_negative) + selected_dislikes

    if inputs.dedupe:
        positive_parts = dedupe_preserve_order(positive_parts)
        negative_parts = dedupe_preserve_order(negative_parts)

    if inputs.shuffle_positive:
        generated_parts = positive_parts[len(base_positive_parts) :]
        rng.shuffle(generated_parts)
        positive_parts = base_positive_parts + generated_parts

    joiner = separator_for(inputs.separator)
    selected = format_selected(
        seed=inputs.seed,
        likes=selected_likes,
        dislikes=selected_dislikes,
        characters=selected_characters,
        clothing=selected_clothing,
        styles=selected_styles,
        extra=selected_extra,
    )

    return WildcardResult(
        positive_prompt=joiner.join(positive_parts),
        negative_prompt=joiner.join(negative_parts),
        selected=selected,
    )


def clean_base(text: str) -> list[str]:
    cleaned = text.strip()
    return [cleaned] if cleaned else []


def sample_lines(rng: random.Random, text: str, count: int) -> list[str]:
    choices = parse_lines(text)
    if count <= 0 or not choices:
        return []
    return rng.sample(choices, k=min(count, len(choices)))


def parse_lines(text: str) -> list[str]:
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return lines


def dedupe_preserve_order(items: list[str]) -> list[str]:
    seen = set()
    deduped = []
    for item in items:
        key = item.casefold()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def separator_for(separator: str) -> str:
    if separator == "space":
        return " "
    if separator == "newline":
        return "\n"
    return ", "


def format_selected(seed: int, **categories: list[str]) -> str:
    sections = [f"seed: {seed}"]
    for name, items in categories.items():
        sections.append(f"\n{name}:")
        if items:
            sections.extend(f"- {item}" for item in items)
        else:
            sections.append("- <none>")
    return "\n".join(sections)
