from __future__ import annotations

import unittest
from unittest.mock import patch

from nodes import PiLLMText


class PiLLMTextNodeTests(unittest.TestCase):
    def test_saved_text_if_present_skips_pi_call(self):
        node = PiLLMText()

        with patch("nodes.resolve_pi_response") as resolve_pi_response:
            result = node.generate(
                system_instruction="sys",
                model_name="minimax/MiniMax-M3",
                prompt="prompt",
                response_mode="use_saved_text_if_present",
                cache_mode="use_cache_or_generate",
                saved_response=" saved output ",
                seed=0,
                timeout_seconds=120,
                run_every_queue=False,
            )

        resolve_pi_response.assert_not_called()
        self.assertEqual(result, ("saved output",))

    def test_saved_text_if_present_generates_when_saved_text_is_empty(self):
        node = PiLLMText()

        with patch("nodes.resolve_pi_response", return_value="live output") as resolve_pi_response:
            result = node.generate(
                system_instruction="sys",
                model_name="minimax/MiniMax-M3",
                prompt="prompt",
                response_mode="use_saved_text_if_present",
                cache_mode="use_cache_or_generate",
                saved_response=" ",
                seed=0,
                timeout_seconds=120,
                run_every_queue=False,
            )

        resolve_pi_response.assert_called_once()
        self.assertEqual(result, ("live output",))


if __name__ == "__main__":
    unittest.main()
