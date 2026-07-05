from __future__ import annotations

import unittest

from pi_runner import (
    RESPONSE_MODE_CALL_PI,
    RESPONSE_MODE_USE_SAVED_TEXT,
    RESPONSE_MODE_USE_SAVED_TEXT_IF_PRESENT,
    PiRequest,
    build_pi_command,
    build_prompt,
    should_use_saved_response,
)


class PiRunnerTests(unittest.TestCase):
    def test_build_prompt_joins_non_empty_parts_with_blank_lines(self):
        self.assertEqual(build_prompt(" first ", "", "second", "  "), "first\n\nsecond")

    def test_build_pi_command_uses_text_only_print_mode(self):
        command = build_pi_command(
            PiRequest(
                system_instruction="return only text",
                model_name="minimax/MiniMax-M3",
                prompt="hello",
            )
        )

        self.assertEqual(
            command,
            [
                "pi",
                "-p",
                "--no-tools",
                "--no-context-files",
                "--no-session",
                "--system-prompt",
                "return only text",
                "--model",
                "minimax/MiniMax-M3",
                "hello",
            ],
        )

    def test_build_pi_command_omits_empty_model_name(self):
        command = build_pi_command(
            PiRequest(system_instruction="sys", model_name="  ", prompt="prompt")
        )

        self.assertNotIn("--model", command)
        self.assertEqual(command[-1], "prompt")

    def test_saved_response_modes(self):
        self.assertFalse(should_use_saved_response(RESPONSE_MODE_CALL_PI, "saved"))
        self.assertTrue(should_use_saved_response(RESPONSE_MODE_USE_SAVED_TEXT, ""))
        self.assertFalse(
            should_use_saved_response(RESPONSE_MODE_USE_SAVED_TEXT_IF_PRESENT, "  ")
        )
        self.assertTrue(
            should_use_saved_response(RESPONSE_MODE_USE_SAVED_TEXT_IF_PRESENT, "saved")
        )


if __name__ == "__main__":
    unittest.main()
