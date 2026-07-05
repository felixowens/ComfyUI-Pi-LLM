# ComfyUI Pi LLM

A small ComfyUI custom node that calls the local `pi` CLI in print mode and returns the LLM response as a `STRING`.

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

## Behavior

The node runs Pi as:

```bash
pi -p --no-tools --no-context-files --no-session --system-prompt "..." --model "minimax/MiniMax-M3" "...prompt..."
```

Tools, context files, and sessions are disabled so the node behaves like a text-only LLM call and avoids file/system side effects. The `seed` is used for ComfyUI cache invalidation; Pi does not currently receive it as a model sampling seed.

## Requirements

- Pi must be installed and available on the `PATH` used by the ComfyUI process.
- Pi must already be authenticated/configured for the selected model/provider.

You can test Pi outside ComfyUI with:

```bash
pi -p --no-tools --no-context-files --no-session "Say hello in five words."
```

After installing this node, restart ComfyUI and look for `Pi > Pi LLM Text`.

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
