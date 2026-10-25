"""Writes each episode's <lang>.md as a blog post into a website, and copies
the images it references, rewriting their paths. The episodes' numbers
become the publication plan. With --check, writes nothing and fails if the
website differs from what it would write. See ../README.md.

    blog.py --posts <dir> --images <dir> --images-url <path> --plan <file> [--check]
"""

import argparse
import os
import re
import sys
from pathlib import Path

from post import ADDRESS, COMMENT_PROMPT, DOCS_SITE, EPISODES, EpisodeError, docs_chapter, episode_folders, episode_id

DOCS_LINK = {
    "en": lambda chapter, tested: f"More in the git-splice docs{', where every command is tested' if tested else ''}: {chapter}.",
    "de": lambda chapter, tested: f"Mehr dazu in der Dokumentation von git-splice{', in der jeder Befehl getestet ist' if tested else ''} (auf Englisch): {chapter}.",
}
LANGS = ("de", "en")


def frontmatter_field(text: str, field: str, pattern: str = r"(\S+)") -> str | None:
    match = re.match(rf"---\n(?:.*\n)*?{field}: *{pattern}\n(?:.*\n)*?---\n", text)
    return match.group(1) if match else None


def docs_paragraph(source: Path, path: str, lang: str) -> str:
    """The link to the chapter of the git-splice docs an episode goes with."""
    chapter = docs_chapter(source, path)
    url = f"https://{DOCS_SITE}/" + (f"{chapter.page}/" if chapter.page else "")
    return DOCS_LINK[lang](f"[{chapter.title}]({url})", chapter.tested)


def build(episodes: Path, posts: Path, images: Path, images_url: str, plan: Path) -> tuple[dict[Path, bytes], list[Path]]:
    """What to write where, and which stale files to remove."""
    outputs: dict[Path, bytes] = {}
    image_sources: dict[str, Path] = {}
    folders = episode_folders(episodes)

    for folder in folders:
        for source in sorted(folder.glob("[a-z][a-z].md")):
            where = source.relative_to(episodes)
            try:
                outputs[posts / source.stem / f"{slug(source)}.svx"] = post(source, images_url, image_sources).encode()
            except EpisodeError as error:
                raise EpisodeError(f"{where}: {error}") from None
    for name, file in image_sources.items():
        outputs[images / name] = file.read_bytes()

    plan_ids = "".join(f'\t"{episode_id(folder)}",\n' for folder in folders)
    outputs[plan] = f"""export const publicationPlan: string[] = [{f"\n{plan_ids}" if plan_ids else ""}];

export const plannedPosition = (id: string) => {{
\tconst position = publicationPlan.indexOf(id);
\treturn position === -1 ? publicationPlan.length : position;
}};
""".encode()

    # The images folder belongs to the episodes; posts outside them stay untouched.
    stray = [path for path in sorted(images.iterdir()) if path not in outputs] if images.exists() else []
    # A post of an episode whose slug changed: the episode now writes it under its new name.
    ids = {episode_id(folder) for folder in folders}
    for lang in LANGS:
        if (posts / lang).exists():
            stray += [
                path
                for path in sorted((posts / lang).glob("*.svx"))
                if path not in outputs and frontmatter_id(path) in ids
            ]
    return outputs, stray


def slug(source: Path) -> str:
    """The post's file name: its title, written for a URL, unless the frontmatter pins it."""
    text = source.read_text()
    if pinned := frontmatter_field(text, "slug"):
        return pinned
    if re.search(r"^publishedAt:", text, re.MULTILINE):
        raise EpisodeError("a published episode pins its slug, so retitling it keeps its URL")
    title = frontmatter_field(text, "title", r'"?(.*?)"?')
    if not title:
        raise EpisodeError("frontmatter needs a title")
    return slugify(title)


def slugify(title: str) -> str:
    """Sync state belongs in the worktree -> sync-state-belongs-in-the-worktree; ä -> ae, ß -> ss."""
    text = title.lower()
    for letter, spelled in {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}.items():
        text = text.replace(letter, spelled)
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def frontmatter_id(path: Path) -> str | None:
    match = re.search(r"^id: *(\S+)$", path.read_text(), re.MULTILINE)
    return match.group(1) if match else None


def post(source: Path, images_url: str, image_sources: dict[str, Path]) -> str:
    """The episode as a blog post: the frontmatter the website reads, and the ending the video has too."""
    text = source.read_text()
    end = text.find("\n---\n", 4)
    if re.search(r"^id:", text[:end] if end != -1 else text[:-1], re.MULTILINE):
        raise EpisodeError("drop the id, the build takes it from the folder name")
    docs = frontmatter_field(text, "docs")
    question = frontmatter_field(text, "question", r'"?(.*?)"?')
    if not question and re.search(r"^publishedAt:", text, re.MULTILINE):
        raise EpisodeError("a published episode ends with a question to the viewer, in its frontmatter")
    lang = source.stem

    def image(match: re.Match) -> str:
        alt, path = match.groups()
        if re.match(r"[a-z]+:|/", path):
            return match.group(0)
        file = (source.parent / path).resolve()
        if not file.exists():
            raise EpisodeError(f"no image at {path}")
        known = image_sources.get(file.name)
        if known and known != file:
            raise EpisodeError(f"{path} and {known.relative_to(source.parent.parent)} share the name {file.name}")
        image_sources[file.name] = file
        return f"![{alt}]({images_url}/{file.name})"

    text = re.sub(r"^---\n", f"---\nid: {episode_id(source.parent)}\n", text, count=1)
    for field in (r"slug: *\S+", r"docs: *\S+", r"question: .*"):
        text = re.sub(rf"^{field}\n", "", text, count=1, flags=re.MULTILINE)
    # A code block's # address line is for the video, which shows it by a QR
    # code; the post links to it in its prose or its docs link.
    text = re.sub(rf"^(```[A-Za-z0-9_]*\n){ADDRESS}\n", r"\1", text, flags=re.MULTILINE)
    text = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", image, text)
    if docs:
        text += f"\n{docs_paragraph(source, docs, lang)}\n"
    if question:
        text += f"\n**{question}** {COMMENT_PROMPT[lang]}\n"
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--posts", type=Path, required=True, help="where <lang>/<slug>.svx go")
    parser.add_argument("--images", type=Path, required=True, help="where the posts' images go")
    parser.add_argument("--images-url", required=True, help="the path the website serves the images at")
    parser.add_argument("--plan", type=Path, required=True, help="the publication plan, a TypeScript module")
    parser.add_argument("--check", action="store_true", help="write nothing, fail if out of date")
    args = parser.parse_args()
    posts, images, plan = (path.resolve() for path in (args.posts, args.images, args.plan))
    try:
        outputs, stray = build(EPISODES, posts, images, args.images_url, plan)
    except EpisodeError as error:
        sys.exit(f"blog: {error}")
    if args.check:
        stale = [path for path, content in outputs.items() if not path.exists() or path.read_bytes() != content]
        if stale + stray:
            listed = "\n".join(f"  {os.path.relpath(path)}" for path in stale + stray)
            sys.exit(f"blog: out of date, run 'just episodes':\n{listed}")
        return
    for path in stray:
        path.unlink()
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


if __name__ == "__main__":
    main()
