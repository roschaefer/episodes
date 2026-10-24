"""Renders an episode's en.md as a video, block by block.

A block starts at each heading, diagram, or code block, and its narration is
the prose up to the next one. A paragraph ending in a colon introduces the
next block, so it plays over that one. The prose before the first block plays
over a title card. Each language's <lang>.md makes its own video. See ../README.md.

    EPISODE=<id> [EPISODE_LANG=en|de] [VOICE=piper|silence|recorder] manim video/episode.py Episode
"""

import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from manim import DOWN, WHITE, Code, FadeIn, FadeOut, Mobject, SVGMobject, Text, VGroup, config
from manim_voiceover import VoiceoverScene
import manim_voiceover.services.base as voiceover_base
from manim_voiceover.services.base import SpeechService
from pydub import AudioSegment

EPISODES = Path(__file__).resolve().parent.parent
GIT_SPLICE = EPISODES / "git-splice"
DOCS_SITE = "roschaefer.github.io/git-splice"
WORDS_PER_MINUTE = 150
# Seconds of quiet after a paragraph, and after the last one a block shows.
PARAGRAPH_PAUSE = 0.6
BLOCK_PAUSE = 1.2
COMMENT_PROMPT = {"en": "Write it in the comments below.", "de": "Schreibt es mir in die Kommentare."}
DOCS_LABEL = {"en": "More in the git-splice docs", "de": "Mehr in der Dokumentation von git-splice"}
PIPER_VOICE = {"en": "en_US-lessac-medium", "de": "de_DE-thorsten-medium"}

config.background_color = WHITE


@dataclass
class Block:
    kind: str  # "title", "heading", "image", "code", "docs" or "question"
    content: str
    narration: list[str] = field(default_factory=list)


def spoken(markdown: str) -> str:
    """The prose as I'd read it out: no Markdown syntax."""
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", markdown)
    text = re.sub(r"[`*_]", "", text)
    text = re.sub(r"^\s*[-+] ", "", text, flags=re.MULTILINE)
    return " ".join(text.split())


def parse(path: Path) -> list[Block]:
    lang = path.stem
    _, frontmatter, body = path.read_text().split("---\n", 2)
    title = re.search(r'^title: *"?(.*?)"?$', frontmatter, re.MULTILINE).group(1)
    blocks = [Block("title", title)]
    docs = re.search(r"^docs: *(\S+)$", frontmatter, re.MULTILINE)
    question = re.search(r'^question: *"?(.*?)"?$', frontmatter, re.MULTILINE)
    paragraph: list[str] = []

    lead_in: list[str] = []

    def end_paragraph() -> None:
        if paragraph:
            blocks[-1].narration.extend(lead_in)
            lead_in.clear()
            text = spoken("\n".join(paragraph))
            (lead_in if text.endswith(":") else blocks[-1].narration).append(text)
            paragraph.clear()

    def start(block: Block) -> None:
        end_paragraph()
        block.narration.extend(lead_in)
        lead_in.clear()
        blocks.append(block)

    lines = iter(body.splitlines())
    for line in lines:
        if line.startswith("```"):
            code = []
            for code_line in lines:
                if code_line.startswith("```"):
                    break
                code.append(code_line)
            start(Block("code", "\n".join(code)))
        elif image := re.fullmatch(r"!\[[^\]]*\]\(([^)]+)\)", line.strip()):
            start(Block("image", str((path.parent / image.group(1)).resolve())))
        elif heading := re.fullmatch(r"#+ +(.*)", line):
            start(Block("heading", spoken(heading.group(1))))
        elif line.strip():
            paragraph.append(line)
        else:
            end_paragraph()
    end_paragraph()
    blocks[-1].narration.extend(lead_in)
    if docs:
        chapter = (path.parent / docs.group(1)).resolve()
        chapter_title = spoken(re.search(r"^# +(.+)$", chapter.read_text(), re.MULTILINE).group(1))
        # Its page on the docs site, as I'd type it: no scheme, a README is its folder.
        page = re.sub(r"(^|/)README\.md$|\.md$", "", str(chapter.relative_to(GIT_SPLICE.resolve())))
        url = f"{DOCS_SITE}/{page}".rstrip("/")
        blocks.append(Block("docs", f"{DOCS_LABEL[lang]}\n{chapter_title}\n{url}"))
    if question:
        prompt = COMMENT_PROMPT[lang]
        blocks.append(Block("question", f"{question.group(1)}\n{prompt}", [f"{question.group(1)} {prompt}"]))
    return blocks


def find_episode(name: str, episodes: Path = EPISODES) -> Path:
    """The episode folder, by its full name (01-submodule-problems), id, or number."""
    folders = sorted(path.parent for path in episodes.glob("[0-9]*-*/en.md"))
    for folder in folders:
        number, id = folder.name.split("-", 1)
        if name in (folder.name, id) or name.lstrip("0") == number.lstrip("0"):
            return folder
    raise SystemExit(f"No episode {name!r}. Episodes: {', '.join(folder.name for folder in folders)}")


def append_new_take(json_file, entry) -> None:
    """manim-voiceover lists a voiceover in cache.json on every render, even one it found there."""
    cache = Path(json_file)
    if cache.exists() and any(take["input_data"] == entry["input_data"] for take in json.loads(cache.read_text())):
        return
    append_voiceover_cache_entry(json_file, entry)


append_voiceover_cache_entry = voiceover_base.append_voiceover_cache_entry
voiceover_base.append_voiceover_cache_entry = append_new_take


class GeneratedVoice(SpeechService):
    """A voice made from the text, to preview before recording."""

    service = ""

    def generate_from_text(self, text, cache_dir=None, path=None, **kwargs):
        cache_dir = Path(cache_dir or self.cache_dir)
        input_data = {"input_text": text, "service": self.service}
        cached = self.get_cached_result(input_data, cache_dir)
        if cached is not None:
            return cached
        audio_path = self.get_audio_basename(input_data) + ".wav"
        self.synthesize(text, cache_dir / audio_path)
        return {"input_text": text, "input_data": input_data, "original_audio": audio_path}


class Silence(GeneratedVoice):
    """Silence as long as reading the text would take."""

    service = "silence"

    def synthesize(self, text: str, out: Path) -> None:
        seconds = max(1.5, len(text.split()) / WORDS_PER_MINUTE * 60)
        AudioSegment.silent(duration=int(seconds * 1000)).export(out, format="wav")


class Piper(GeneratedVoice):
    """A computer voice, offline, so drafts stay on this machine."""

    service = "piper"

    def __init__(self, lang: str, **kwargs):
        self.model = Path(os.environ["PIPER_VOICES"]) / f"{PIPER_VOICE[lang]}.onnx"
        super().__init__(**kwargs)

    def synthesize(self, text: str, out: Path) -> None:
        subprocess.run(
            [os.environ["PIPER"], "--model", self.model, "--output-file", out],
            input=text,
            text=True,
            check=True,
            capture_output=True,
        )


def default_stroke_width(svg: str) -> str:
    """Gives each stroked shape without a stroke-width SVG's default, 1.

    draw.io leaves the attribute out of 1px lines, and Manim would draw
    them 0 wide, so the boxes of a folder layout would vanish.
    """
    return re.sub(
        r'<(rect|path|ellipse|circle|line|polyline|polygon)\b(?![^>]*\bstroke-width=)(?=[^>]*\bstroke="(?!none)[^"]*")',
        r'<\1 stroke-width="1"',
        svg,
    )


def plain_svg(path: Path) -> Path:
    """The SVG as Manim can draw it.

    draw.io colors shapes with CSS light-dark() and var(), which Manim
    can't parse, over plain fill and stroke attributes for light mode, so
    the CSS goes, and so does the background, which Manim sizes as if
    100% were 100 units. Manim doesn't draw <text>, so Inkscape turns it
    into paths.
    """
    svg = path.read_text()
    svg = re.sub(r"<style[^>]*>.*?</style>", "", svg, flags=re.DOTALL)
    svg = re.sub(r' style="[^"]*"', "", svg)
    svg = re.sub(r'<rect [^>]*width="100%"[^>]*/>', "", svg)
    svg = default_stroke_width(svg)
    out_dir = EPISODES / "media" / "svg"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{path.stem}-{hashlib.sha256(svg.encode()).hexdigest()[:8]}.svg"
    if not out.exists():
        stripped = out.with_suffix(".in.svg")
        stripped.write_text(svg)
        subprocess.run(
            ["inkscape", "--export-text-to-path", "--export-plain-svg", f"--export-filename={out}", stripped],
            check=True,
            capture_output=True,
        )
        stripped.unlink()
    return out


def visual(block: Block) -> Mobject:
    if block.kind == "title":
        return Text(block.content, color="#081421", font_size=56)
    if block.kind == "heading":
        return Text(block.content, color="#0a6b9c", font_size=44)
    if block.kind == "docs":
        label, chapter_title, url = block.content.split("\n")
        return VGroup(
            Text(label, color="#5d7189", font_size=32),
            Text(chapter_title, color="#081421", font_size=48),
            Text(url, color="#0a6b9c", font_size=24),
        ).arrange(DOWN, buff=0.4)
    if block.kind == "question":
        question, prompt = block.content.split("\n")
        # One sentence per line, so a question of two sentences stays readable.
        sentences = re.split(r"(?<=[?.!]) +", question)
        return VGroup(
            VGroup(*(Text(sentence, color="#081421", font_size=44) for sentence in sentences)).arrange(DOWN, buff=0.2),
            Text(prompt, color="#5d7189", font_size=32),
        ).arrange(DOWN, buff=0.6)
    if block.kind == "image":
        return SVGMobject(plain_svg(Path(block.content)))
    return Code(
        code_string=block.content,
        language="console",
        background="window",
        add_line_numbers=False,
        paragraph_config={"font_size": 32},
    )


def framed(block: Block) -> Mobject:
    """The block's visual, sized to fit the frame."""
    mobject = visual(block)
    if block.kind in ("image", "code") or mobject.width > 12:
        mobject.scale_to_fit_width(12)
    if mobject.height > 6.5:
        mobject.scale_to_fit_height(6.5)
    return mobject


if "EPISODE" in os.environ:
    # Only my own voice makes the video; a preview says which voice it has.
    voice = os.environ.get("VOICE", "piper")
    suffix = "" if voice == "recorder" else f"-{voice}"
    config.output_file = f"{find_episode(os.environ['EPISODE']).name}-{os.environ.get('EPISODE_LANG', 'en')}{suffix}"


class Episode(VoiceoverScene):
    def construct(self) -> None:
        episode = find_episode(os.environ["EPISODE"])
        lang = os.environ.get("EPISODE_LANG", "en")
        voiceovers = episode / "voiceovers" / lang
        voiceovers.mkdir(parents=True, exist_ok=True)
        voice = os.environ.get("VOICE", "piper")
        if voice == "recorder":
            from recorder import PipeWireRecorder

            self.set_speech_service(PipeWireRecorder(cache_dir=voiceovers, transcription_model=None))
        else:
            if voice == "piper":
                self.set_speech_service(Piper(lang, cache_dir=voiceovers / voice))
            else:
                self.set_speech_service(Silence(cache_dir=voiceovers / voice))

        shown: Mobject | None = None
        for block in parse(episode / f"{lang}.md"):
            mobject = framed(block)
            transition = [FadeIn(mobject)] + ([FadeOut(shown)] if shown else [])
            if not block.narration:
                self.play(*transition)
                self.wait(3 if block.kind == "docs" else 1)
            for index, paragraph in enumerate(block.narration):
                with self.voiceover(text=paragraph) as tracker:
                    if index == 0:
                        self.play(*transition, run_time=min(1, tracker.duration))
                self.wait(BLOCK_PAUSE if index == len(block.narration) - 1 else PARAGRAPH_PAUSE)
            shown = mobject
        self.play(FadeOut(shown))

