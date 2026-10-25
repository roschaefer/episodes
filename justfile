# Recipes use bash, like the dev shell's commands.
set shell := ["bash", "-cu"]

# Runs a command inside the Nix dev shell, which has what uv doesn't install
shell := "nix develop . --command bash -c"

default:
    @just --list

# Run the checks of the episodes, their videos' glue, and the git-splice docs they cite
check: video-test voiceovers-check
    cd git-splice && nix develop --command just docs-check

# Preview an episode's video in a language (en, de) with a computer voice (voice=silence for none): quality l(ow), m(edium), h(igh) or k (4K)
video id lang="en" quality="l" voice="piper":
    {{shell}} 'EPISODE={{id}} EPISODE_LANG={{lang}} VOICE={{voice}} uv run manim -q{{quality}} video/episode.py Episode'

# Record the voiceover of each paragraph not recorded yet in a language (en, de), then render that video in full HD
record id lang="en":
    {{shell}} 'EPISODE={{id}} EPISODE_LANG={{lang}} VOICE=recorder uv run manim -qh video/episode.py Episode'

# Render an episode's slides in a language (en, de) as a PDF, one page per block of the video: quality l(ow), m(edium), h(igh) or k (4K)
slides id lang="en" quality="h":
    {{shell}} 'uv run python video/slides.py {{id}} {{lang}} {{quality}}'

# List an episode's paragraphs in a language, numbered, and which of them I've recorded
voiceovers id lang="en":
    {{shell}} 'uv run python video/voiceovers.py status {{id}} {{lang}}'

# Discard my takes of the given paragraphs in a language, so that the next 'just record' asks for them again
retake id lang +paragraphs:
    {{shell}} 'uv run python video/voiceovers.py retake {{id}} {{lang}} {{paragraphs}}'

# Discard takes of text the episode no longer has
voiceovers-prune id:
    {{shell}} 'uv run python video/voiceovers.py prune {{id}}'

# Fail if an episode has takes of text it no longer has, or a block nothing is said over
voiceovers-check:
    {{shell}} 'uv run python video/voiceovers.py check'

# Write each episode as a blog post into a website: <posts>/<lang>/<slug>.svx, the images to <images>, served at <images_url>, and the series they make to <series>; with --check, fail if they are out of date
blog posts images images_url series *check:
    {{shell}} 'uv run python video/blog.py --posts {{posts}} --images {{images}} --images-url {{images_url}} --series {{series}} {{check}}'

# Test the glue that turns an episode into video blocks and a blog post
video-test:
    {{shell}} 'uv run pytest -q video'
