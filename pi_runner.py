from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PiRequest:
    system_instruction: str
    model_name: str
    prompt: str
    image_paths: tuple[str, ...] = ()
    image_digests: tuple[str, ...] = ()


RESPONSE_MODE_CALL_PI = "call_pi"
RESPONSE_MODE_USE_SAVED_TEXT = "use_saved_text"
RESPONSE_MODE_USE_SAVED_TEXT_IF_PRESENT = "use_saved_text_if_present"
RESPONSE_MODES = [
    RESPONSE_MODE_USE_SAVED_TEXT_IF_PRESENT,
    RESPONSE_MODE_CALL_PI,
    RESPONSE_MODE_USE_SAVED_TEXT,
]
DEFAULT_RESPONSE_MODE = RESPONSE_MODE_USE_SAVED_TEXT_IF_PRESENT

CACHE_MODE_USE_CACHE_OR_GENERATE = "use_cache_or_generate"
CACHE_MODE_REFRESH_CACHE = "refresh_cache"
CACHE_MODE_CACHE_ONLY = "cache_only"
CACHE_MODE_DISABLE_CACHE = "disable_cache"
CACHE_MODES = [
    CACHE_MODE_USE_CACHE_OR_GENERATE,
    CACHE_MODE_REFRESH_CACHE,
    CACHE_MODE_CACHE_ONLY,
    CACHE_MODE_DISABLE_CACHE,
]
DEFAULT_CACHE_MODE = CACHE_MODE_USE_CACHE_OR_GENERATE
CACHE_SCHEMA_VERSION = 1
DEFAULT_CACHE_DIR = Path(__file__).resolve().parent / "cache"


def should_use_saved_response(response_mode: str, saved_response: str) -> bool:
    """Return whether the LLM node should skip Pi and output saved text."""
    if response_mode == RESPONSE_MODE_USE_SAVED_TEXT:
        return True
    if response_mode == RESPONSE_MODE_USE_SAVED_TEXT_IF_PRESENT:
        return bool(saved_response.strip())
    return False


def build_cache_key(request: PiRequest, seed: int) -> str:
    """Build a stable cache key from all inputs that affect the LLM request."""
    payload = {
        "schema_version": CACHE_SCHEMA_VERSION,
        "request": {
            "system_instruction": request.system_instruction,
            "model_name": request.model_name,
            "prompt": request.prompt,
            "image_digests": request.image_digests,
        },
        "seed": seed,
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def cache_path_for(cache_key: str, cache_dir: Path = DEFAULT_CACHE_DIR) -> Path:
    return cache_dir / f"{cache_key}.txt"


def read_cached_response(cache_key: str, cache_dir: Path = DEFAULT_CACHE_DIR) -> str | None:
    path = cache_path_for(cache_key, cache_dir)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def write_cached_response(
    cache_key: str, response: str, cache_dir: Path = DEFAULT_CACHE_DIR
) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path_for(cache_key, cache_dir).write_text(response, encoding="utf-8")


def resolve_pi_response(
    request: PiRequest,
    seed: int,
    timeout_seconds: int,
    cache_mode: str = DEFAULT_CACHE_MODE,
    cache_dir: Path = DEFAULT_CACHE_DIR,
) -> str:
    """Return a Pi response using the deterministic local cache when requested."""
    cache_key = build_cache_key(request, seed)

    if cache_mode in (CACHE_MODE_USE_CACHE_OR_GENERATE, CACHE_MODE_CACHE_ONLY):
        cached = read_cached_response(cache_key, cache_dir)
        if cached is not None:
            return cached
        if cache_mode == CACHE_MODE_CACHE_ONLY:
            raise FileNotFoundError(f"No cached Pi response found for key {cache_key}.")

    response = run_pi_request(request, timeout_seconds=timeout_seconds)

    if cache_mode != CACHE_MODE_DISABLE_CACHE:
        write_cached_response(cache_key, response, cache_dir)

    return response


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

    command.extend(f"@{image_path}" for image_path in request.image_paths)
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
