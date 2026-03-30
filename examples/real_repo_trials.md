# Real Repo Trials

This note records a small set of real GitHub repository trials used to validate the main skill's README-first behavior.

## Repositories

### `openai/whisper`

- Repository: [https://github.com/openai/whisper](https://github.com/openai/whisper)
- README-selected goal: documented inference
- README-selected command: `whisper audio.flac audio.mp3 audio.wav --model turbo`
- Outcome: `blocked`
- Main blocker: the `whisper` executable was not available in the current environment

Why this trial mattered:

- The README includes both setup commands and runnable inference examples.
- The skill should prefer the runnable inference entrypoint over `pip install ...`.

### `CompVis/stable-diffusion`

- Repository: [https://github.com/CompVis/stable-diffusion](https://github.com/CompVis/stable-diffusion)
- README-selected goal: documented inference
- README-selected command: `python scripts/txt2img.py --prompt "a photograph of an astronaut riding a horse" --plms`
- Outcome: `partial`
- Main blocker: missing dependency `omegaconf`

Why this trial mattered:

- The README mixes environment setup, asset preparation, and inference commands.
- The skill should record an environment blocker instead of silently patching code or inventing a different run path.

### `facebookresearch/segment-anything`

- Repository: [https://github.com/facebookresearch/segment-anything](https://github.com/facebookresearch/segment-anything)
- README-selected goal: documented inference
- README-selected command: `python scripts/amg.py --checkpoint <path/to/checkpoint> --model-type <model_type> --input <image_or_folder> --output <path/to/output>`
- Outcome: `partial`
- Main blocker: missing local package import `segment_anything`

Why this trial mattered:

- The README contains install commands, export commands, and a runnable inference script.
- The skill should select the documented inference entrypoint, then report missing install state as a run blocker.

## Validation results

What these trials confirmed:

- `repro_outputs/` generation works on real repositories
- README-first target selection now prefers runnable inference entrypoints over setup-only commands
- blocked or partial states are recorded without modifying target repositories
- `PATCHES.md` is not generated when no repo files were changed

What these trials changed in the skill implementation:

- command extraction now records a `kind` field such as `setup`, `asset`, `run`, or `smoke`
- orchestration now scores commands so setup steps do not outrank README-documented inference or evaluation entrypoints
- repository validation ignores temporary trial directories like `tmp/`

## Current limits

- This was a conservative Windows-hosted trial pass, not a full benchmark across Linux GPU environments.
- The helper scripts do not yet build full environment plans directly from README sections.
- Asset-heavy repositories still stop at documented environment or dependency blockers unless setup is explicitly performed.
