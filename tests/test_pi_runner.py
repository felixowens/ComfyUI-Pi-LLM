from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pi_runner import (
    RESPONSE_MODE_CALL_PI,
    RESPONSE_MODE_USE_SAVED_TEXT,
    CACHE_MODE_CACHE_ONLY,
    CACHE_MODE_DISABLE_CACHE,
    CACHE_MODE_REFRESH_CACHE,
    CACHE_MODE_USE_CACHE_OR_GENERATE,
    RESPONSE_MODE_USE_SAVED_TEXT_IF_PRESENT,
    PiRequest,
    build_cache_key,
    build_pi_command,
    build_prompt,
    read_cached_response,
    resolve_pi_response,
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

    def test_build_cache_key_is_stable_and_seeded(self):
        request = PiRequest(system_instruction="sys", model_name="model", prompt="prompt")

        self.assertEqual(build_cache_key(request, seed=1), build_cache_key(request, seed=1))
        self.assertNotEqual(build_cache_key(request, seed=1), build_cache_key(request, seed=2))

    def test_resolve_pi_response_writes_and_reads_cache(self):
        request = PiRequest(system_instruction="sys", model_name="model", prompt="prompt")

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            with patch("pi_runner.run_pi_request", return_value="live response") as run_pi:
                first = resolve_pi_response(
                    request,
                    seed=1,
                    timeout_seconds=120,
                    cache_mode=CACHE_MODE_USE_CACHE_OR_GENERATE,
                    cache_dir=cache_dir,
                )
                second = resolve_pi_response(
                    request,
                    seed=1,
                    timeout_seconds=120,
                    cache_mode=CACHE_MODE_USE_CACHE_OR_GENERATE,
                    cache_dir=cache_dir,
                )

        self.assertEqual(first, "live response")
        self.assertEqual(second, "live response")
        run_pi.assert_called_once()

    def test_cache_only_raises_when_missing(self):
        request = PiRequest(system_instruction="sys", model_name="model", prompt="prompt")

        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(FileNotFoundError):
                resolve_pi_response(
                    request,
                    seed=1,
                    timeout_seconds=120,
                    cache_mode=CACHE_MODE_CACHE_ONLY,
                    cache_dir=Path(tmpdir),
                )

    def test_refresh_cache_updates_cache(self):
        request = PiRequest(system_instruction="sys", model_name="model", prompt="prompt")

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            with patch("pi_runner.run_pi_request", side_effect=["first", "second"]):
                resolve_pi_response(
                    request,
                    seed=1,
                    timeout_seconds=120,
                    cache_mode=CACHE_MODE_REFRESH_CACHE,
                    cache_dir=cache_dir,
                )
                refreshed = resolve_pi_response(
                    request,
                    seed=1,
                    timeout_seconds=120,
                    cache_mode=CACHE_MODE_REFRESH_CACHE,
                    cache_dir=cache_dir,
                )

            self.assertEqual(refreshed, "second")
            self.assertEqual(read_cached_response(build_cache_key(request, 1), cache_dir), "second")

    def test_disable_cache_does_not_write_cache(self):
        request = PiRequest(system_instruction="sys", model_name="model", prompt="prompt")

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            with patch("pi_runner.run_pi_request", return_value="live"):
                resolve_pi_response(
                    request,
                    seed=1,
                    timeout_seconds=120,
                    cache_mode=CACHE_MODE_DISABLE_CACHE,
                    cache_dir=cache_dir,
                )

            self.assertIsNone(read_cached_response(build_cache_key(request, 1), cache_dir))


if __name__ == "__main__":
    unittest.main()
