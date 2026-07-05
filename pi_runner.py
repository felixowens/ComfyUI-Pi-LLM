from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class PiRequest:
    system_instruction: str
    model_name: str
    prompt: str


RESPONSE_MODE_CALL_PI = "call_pi"
RESPONSE_MODE_USE_SAVED_TEXT = "use_saved_text"
RESPONSE_MODE_USE_SAVED_TEXT_IF_PRESENT = "use_saved_text_if_present"
RESPONSE_MODES = [
    RESPONSE_MODE_USE_SAVED_TEXT_IF_PRESENT,
    RESPONSE_MODE_CALL_PI,
    RESPONSE_MODE_USE_SAVED_TEXT,
]
DEFAULT_RESPONSE_MODE = RESPONSE_MODE_USE_SAVED_TEXT_IF_PRESENT


def should_use_saved_response(response_mode: str, saved_response: str) -> bool:
    """Return whether the LLM node should skip Pi and output saved text."""
    if response_mode == RESPONSE_MODE_USE_SAVED_TEXT:
        return True
    if response_mode == RESPONSE_MODE_USE_SAVED_TEXT_IF_PRESENT:
        return bool(saved_response.strip())
    return False


def build_prompt(*parts: str) -> str:
    """Join non-empty prompt fragments with a blank line."""
    non_empty_parts = [part.strip() for part in parts if part and part.strip()]
    return "\n\n".join(non_empty_parts)


def build_pi_command(request: PiRequest) -> list[str]:
    """Build the text-only Pi print-mode command without invoking a shell."""
    command = [
        "pi",
        "-p",
        "--no-tools",
        "--no-context-files",
        "--no-session",
        "--system-prompt",
        request.system_instruction,
    ]

    if request.model_name.strip():
        command.extend(["--model", request.model_name.strip()])

    command.append(request.prompt)
    return command


def run_pi_request(request: PiRequest, timeout_seconds: int) -> str:
    """Run Pi and return stripped stdout, raising readable errors on failure."""
    command = build_pi_command(request)
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

    return stdout
