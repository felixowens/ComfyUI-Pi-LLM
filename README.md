# ComfyUI Pi LLM

ComfyUI custom nodes for calling [Pi](https://pi.dev) as a text-only LLM from a workflow.

The main node runs the local `pi` CLI in print mode and returns the model response as a ComfyUI `STRING`. A companion extractor node helps remove common LLM wrapper text, such as XML tags or Markdown code fences.

## Features

- Call Pi from ComfyUI with a system instruction, model dropdown, and prompt.
- Defaults to `minimax/MiniMax-M3`.
- Text-only execution: tools, context files, and sessions are disabled for safer/predictable workflow behavior.
- Cache-busting `seed` input so the same prompt can be regenerated.
- Optional `run_every_queue` mode to force reruns.
- Extract generated text from `<prompt>...</prompt>`, code fences, or custom delimiters.

## Requirements

- ComfyUI.
- Pi installed and available on the `PATH` used by the ComfyUI process.
- Pi already authenticated/configured for the model provider you want to use.

Install Pi if needed:

```bash
npm install -g --ignore-scripts @earendil-works/pi-coding-agent
```

Then authenticate/configure Pi as usual, for example:

```bash
pi /login
```

Or use supported provider API key environment variables. See the Pi docs for provider setup.

Verify Pi works outside ComfyUI:

```bash
pi -p --no-tools --no-context-files --no-session "Say hello in five words."
```

## Installation

From your ComfyUI directory:

```bash
cd custom_nodes
git clone https://github.com/felixowens/ComfyUI-Pi-LLM.git
```

Restart ComfyUI, then search for the `Pi` category.

If ComfyUI cannot find `pi`, make sure the shell/service that starts ComfyUI has Pi on its `PATH`. You can also symlink Pi into a common path, for example:

```bash
which pi
# then, if needed:
sudo ln -s /path/to/pi /usr/local/bin/pi
```

## Nodes

### Pi LLM Text

Category: `Pi`

Inputs:

- `system_instruction`: system prompt passed to Pi via `--system-prompt`.
- `model_name`: Pi model selector dropdown, passed via `--model`. Defaults to `minimax/MiniMax-M3`.
- `prompt`: what the LLM should do or produce. Type text here or connect a `STRING` output from another node.
- `connected_text`: optional extra `STRING` input appended after `prompt` when non-empty.
- `seed`: cache-busting seed. Change it to rerun Pi for the same prompt.
- `timeout_seconds`: maximum time to wait for Pi.
- `run_every_queue`: when enabled, disables ComfyUI caching for this node.

Output:

- `text`: generated response as a ComfyUI `STRING`.

Behavior:

```bash
pi -p --no-tools --no-context-files --no-session --system-prompt "..." --model "minimax/MiniMax-M3" "...prompt..."
```

Tools, context files, and sessions are disabled so the node behaves like a text-only LLM call and avoids file/system side effects. The `seed` is used for ComfyUI cache invalidation; Pi does not currently receive it as a model sampling seed.

### Pi Text Extractor

Extracts useful text from an LLM response when the model adds fluff around the generated content.

Inputs:

- `text`: LLM response to extract from.
- `extraction_mode`:
  - `auto`: try XML tag, then code fence, then custom delimiters.
  - `xml_tag`: extract from tags like `<prompt>...</prompt>`.
  - `code_fence`: extract from triple backticks like ```text ... ```.
  - `between_delimiters`: extract between custom start/end markers.
- `xml_tag`: tag name for XML extraction, defaults to `prompt`.
- `fence_language`: optional code fence language. Empty matches any code fence.
- `start_delimiter` / `end_delimiter`: custom markers for delimiter extraction.
- `occurrence`: choose the `first` or `last` match.
- `strip_whitespace`: trims leading/trailing whitespace from extracted text.
- `fail_if_missing`: raise an error if no wrapper is found. If disabled, returns the original text.

Outputs:

- `text`: extracted text, or original text when not found and `fail_if_missing` is disabled.
- `found`: boolean indicating whether an extraction wrapper was found.

Recommended LLM instruction examples:

```text
Return only the final prompt inside <prompt>...</prompt> tags.
```

or:

````text
Return only the final prompt in a ```text code fence.
````

## Model list

The dropdown is currently a static list generated from `pi --list-models` on the original development machine. If your Pi installation has different model access, edit `nodes.py` and update the `model_name` list.

## Development

Run a syntax check from this repository:

```bash
python -m py_compile nodes.py __init__.py
```

## License

No license has been added yet.
