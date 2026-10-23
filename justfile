# Recipes use bash, like the dev shell's commands.
set shell := ["bash", "-cu"]

# Runs a command inside the Nix dev shell, which has what uv doesn't install
shell := "nix develop . --command bash -c"

default:
    @just --list

# Run the checks of the episodes, their videos' glue, and the git-splice docs they cite
check: video-test voiceovers-check examples-check
    cd git-splice && nix develop --command just docs-check

# Preview an episode's video in a language (en, de) with a computer voice (voice=silence for none): quality l(ow), m(edium), h(igh) or k (4K)
video id lang="en" quality="l" voice="piper":
    {{shell}} 'EPISODE={{id}} EPISODE_LANG={{lang}} VOICE={{voice}} uv run manim -q{{quality}} video/episode.py Episode'

# Record the voiceover of each paragraph not recorded yet in a language (en, de), then render that video in full HD
record id lang="en":
    {{shell}} 'EPISODE={{id}} EPISODE_LANG={{lang}} VOICE=recorder uv run manim -qh video/episode.py Episode'

# List an episode's paragraphs in a language, numbered, and which of them I've recorded
voiceovers id lang="en":
    {{shell}} 'uv run python video/voiceovers.py status {{id}} {{lang}}'

# Discard my takes of the given paragraphs in a language, so that the next 'just record' asks for them again
retake id lang +paragraphs:
    {{shell}} 'uv run python video/voiceovers.py retake {{id}} {{lang}} {{paragraphs}}'

# Discard takes of text the episode no longer has
voiceovers-prune id:
    {{shell}} 'uv run python video/voiceovers.py prune {{id}}'

# Fail if an episode has takes of text it no longer has
voiceovers-check:
    {{shell}} 'uv run python video/voiceovers.py check'

# Test the glue that turns an episode into video blocks
video-test:
    {{shell}} 'uv run pytest -q video'

# Build each episode's example, to see that it still builds
examples-check:
    #!/usr/bin/env bash
    set -euo pipefail
    for script in */example.sh; do
      tmp=$(mktemp -d)
      "$script" "$tmp/example" >/dev/null
      rm -rf "$tmp"
      echo "ok   $script"
    done
