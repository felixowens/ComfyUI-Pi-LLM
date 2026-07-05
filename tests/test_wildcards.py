from __future__ import annotations

import random
import unittest

from wildcards import (
    WildcardInputs,
    compose_wildcard_prompt,
    dedupe_preserve_order,
    parse_lines,
    sample_lines,
)


def make_inputs(seed: int = 42, **overrides) -> WildcardInputs:
    values = dict(
        base_prompt="portrait",
        base_negative="low quality",
        likes="bright eyes\nsmile\nfreckles",
        dislikes="blurry\nbad hands",
        characters="wizard\nknight",
        clothing="hoodie\narmor",
        styles="cinematic\nwatercolor",
        extra="rain\nforest",
        seed=seed,
        likes_count=2,
        dislikes_count=1,
        characters_count=1,
        clothing_count=1,
        styles_count=1,
        extra_count=1,
        separator="comma",
        dedupe=True,
        shuffle_positive=False,
    )
    values.update(overrides)
    return WildcardInputs(**values)


class WildcardTests(unittest.TestCase):
    def test_parse_lines_ignores_blanks_and_comments(self):
        self.assertEqual(
            parse_lines("\nalpha\n # comment\n beta \n# nope"), ["alpha", "beta"]
        )

    def test_sample_lines_clamps_count_to_available_choices(self):
        self.assertEqual(sorted(sample_lines(random.Random(1), "a\nb", 99)), ["a", "b"])

    def test_dedupe_preserves_order_case_insensitively(self):
        self.assertEqual(dedupe_preserve_order(["A", "b", "a", "B", "c"]), ["A", "b", "c"])

    def test_compose_is_deterministic_for_same_seed(self):
        first = compose_wildcard_prompt(make_inputs(seed=123))
        second = compose_wildcard_prompt(make_inputs(seed=123))

        self.assertEqual(first, second)

    def test_compose_changes_for_different_seed(self):
        first = compose_wildcard_prompt(make_inputs(seed=123))
        second = compose_wildcard_prompt(make_inputs(seed=124))

        self.assertNotEqual(first, second)

    def test_compose_outputs_positive_negative_and_selected_debug_text(self):
        result = compose_wildcard_prompt(make_inputs(seed=42))

        self.assertTrue(result.positive_prompt.startswith("portrait, "))
        self.assertTrue(result.negative_prompt.startswith("low quality, "))
        self.assertIn("seed: 42", result.selected)
        self.assertIn("likes:", result.selected)
        self.assertIn("dislikes:", result.selected)

    def test_newline_separator(self):
        result = compose_wildcard_prompt(
            make_inputs(
                seed=42,
                likes_count=1,
                characters_count=0,
                clothing_count=0,
                styles_count=0,
                extra_count=0,
                dislikes_count=0,
                separator="newline",
            )
        )

        self.assertNotIn(", ", result.positive_prompt)
        self.assertIn("\n", result.positive_prompt)


if __name__ == "__main__":
    unittest.main()
