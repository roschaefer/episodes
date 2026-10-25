"""Keeps an episode's recordings in step with its script.

    voiceovers.py status <episode> <lang>               which paragraphs are recorded
    voiceovers.py retake <episode> <lang> <paragraph>…  discard takes, to record them again
    voiceovers.py prune <episode>                       discard takes of text the script no longer has
    voiceovers.py check                                 fail if any episode has such takes,
                                                        or a block nothing is said over

A take is a recording in <episode>/voiceovers/<lang>/, listed in its
cache.json under the text it speaks. See ../README.md.
"""

import json
import sys
from pathlib import Path

from episode import EPISODES, find_episode, parse, silent

CACHE = "cache.json"


def languages(episode: Path) -> list[str]:
    return sorted(path.stem for path in episode.glob("[a-z][a-z].md"))


def paragraphs(episode: Path, lang: str) -> list[str]:
    return [paragraph for block in parse(episode / f"{lang}.md") for paragraph in block.narration]


def takes(voiceovers: Path) -> list[dict]:
    cache = voiceovers / CACHE
    return json.loads(cache.read_text()) if cache.exists() else []


def audio_files(take: dict) -> set[str]:
    return {take[key] for key in ("original_audio", "final_audio") if key in take}


def spoken_text(take: dict) -> str:
    return take["input_data"]["input_text"]


def discard(voiceovers: Path, unwanted) -> list[dict]:
    """Removes the takes for which unwanted(take) holds, with their audio."""
    kept, discarded = [], []
    for take in takes(voiceovers):
        (discarded if unwanted(take) else kept).append(take)
    still_used = set().union(*map(audio_files, kept))
    for take in discarded:
        for audio in audio_files(take) - still_used:
            (voiceovers / audio).unlink(missing_ok=True)
    if discarded:
        (voiceovers / CACHE).write_text(json.dumps(kept, indent=2) + "\n")
    return discarded


def stale(voiceovers: Path, script: set[str]) -> tuple[list[dict], list[Path]]:
    """Takes of text the script no longer has, and audio no take refers to."""
    if not voiceovers.is_dir():
        return [], []
    entries = takes(voiceovers)
    used = set().union(*map(audio_files, entries))
    return (
        [take for take in entries if spoken_text(take) not in script],
        [path for path in voiceovers.iterdir() if path.is_file() and path.name not in used | {CACHE}],
    )


def stale_takes(episode: Path) -> list[str]:
    """What check reports: only the recordings, the generated voices aren't in Git."""
    found = []
    for lang in languages(episode):
        old, unused = stale(episode / "voiceovers" / lang, set(paragraphs(episode, lang)))
        found += [f"{lang}: {spoken_text(take)[:60]}…" for take in old]
        found += [f"{lang}: {path.name}, in no {CACHE}" for path in unused]
    return found


def silent_blocks(episode: Path) -> list[str]:
    """What check reports besides stale takes: blocks with nothing said over them."""
    return [
        f"{lang}: nothing is said over {block.kind} {block.content.splitlines()[0][:50]!r}, give it a paragraph of its own"
        for lang in languages(episode)
        for block in silent(parse(episode / f"{lang}.md"))
    ]


def status(episode: Path, lang: str) -> None:
    recorded = {spoken_text(take) for take in takes(episode / "voiceovers" / lang)}
    script = paragraphs(episode, lang)
    for number, paragraph in enumerate(script, 1):
        print(f"{number:3}  {'✓' if paragraph in recorded else '·'}  {paragraph[:70]}")
    print(f"\n{sum(p in recorded for p in script)} of {len(script)} paragraphs recorded.")
    if stale_takes(episode):
        print(f"Takes of text the script no longer has: run 'just voiceovers-prune {episode.name[:2]}'.")


def retake(episode: Path, lang: str, numbers: list[int]) -> None:
    script = paragraphs(episode, lang)
    if bad := [n for n in numbers if not 1 <= n <= len(script)]:
        raise SystemExit(f"No paragraph {', '.join(map(str, bad))}: {episode.name} has {len(script)}.")
    texts = {script[n - 1] for n in numbers}
    discarded = discard(episode / "voiceovers" / lang, lambda take: spoken_text(take) in texts)
    print(f"Discarded {len(discarded)} take(s). 'just record {episode.name[:2]} {lang}' asks for them again.")


def prune(episode: Path) -> None:
    count = 0
    for lang in languages(episode):
        script = set(paragraphs(episode, lang))
        for voiceovers in [episode / "voiceovers" / lang, *(episode / "voiceovers" / lang).glob("*/")]:
            old, unused = stale(voiceovers, script)
            count += len(discard(voiceovers, lambda take: take in old)) + len(unused)
            for path in unused:
                path.unlink()
    print(f"Discarded {count} take(s) and file(s).")


def check(episodes: Path = EPISODES) -> None:
    problems = {}
    for episode in sorted(path.parent for path in episodes.glob("[0-9]*-*/en.md")):
        if old := stale_takes(episode):
            old.append(f"run 'just voiceovers-prune {episode.name[:2]}' to discard these takes")
        if found := old + silent_blocks(episode):
            problems[episode.name] = found
    for name, found in problems.items():
        print(f"{name}:", *found, sep="\n  ")
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    command, *args = sys.argv[1:] or ["help"]
    if command == "check":
        check()
    elif command == "status" and len(args) == 2:
        status(find_episode(args[0]), args[1])
    elif command == "prune" and len(args) == 1:
        prune(find_episode(args[0]))
    elif command == "retake" and len(args) >= 3 and all(arg.isdigit() for arg in args[2:]):
        retake(find_episode(args[0]), args[1], [int(arg) for arg in args[2:]])
    else:
        raise SystemExit(__doc__)
