"""What an episode's <lang>.md says, before the video or the blog shows it."""

import re
from dataclasses import dataclass
from pathlib import Path

EPISODES = Path(__file__).resolve().parent.parent
GIT_SPLICE = EPISODES / "git-splice"
DOCS_SITE = "roschaefer.github.io/git-splice"
COMMENT_PROMPT = {"en": "Write it in the comments below.", "de": "Schreibt es mir in die Kommentare."}
# A code block's first line "# example.org/page": an address for viewers, not code.
ADDRESS = r"# (\S+\.\S+)"


class EpisodeError(Exception):
    """An episode the blog and the video can't be made from."""


def episode_folders(episodes: Path = EPISODES) -> list[Path]:
    return sorted(path for path in episodes.iterdir() if path.is_dir() and re.match(r"\d+-", path.name))


def episode_id(folder: Path) -> str:
    return folder.name.split("-", 1)[1]


@dataclass
class Chapter:
    """A chapter of the git-splice docs an episode goes with."""

    title: str
    # Its page on the docs site: its path without .md, a README is its folder.
    page: str
    # Whether its commands run as tests.
    tested: bool


def docs_chapter(post: Path, path: str) -> Chapter:
    """The chapter at path, relative to the post."""
    chapter = (post.parent / path).resolve()
    if not chapter.is_relative_to(GIT_SPLICE.resolve()) or not chapter.is_file():
        raise EpisodeError(f"docs must be a chapter in git-splice/, not {path}")
    text = chapter.read_text()
    title = re.search(r"^# +(.+)$", text, re.MULTILINE)
    if not title:
        raise EpisodeError(f"{path} has no # title")
    page = re.sub(r"(^|/)README\.md$|\.md$", "", str(chapter.relative_to(GIT_SPLICE.resolve())))
    return Chapter(title.group(1), page, "```scrut" in text)
