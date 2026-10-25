from pathlib import Path

import pytest
from blog import build
from post import EpisodeError

POST = """---
slug: example
title: "What goes wrong"
---

The intro.
"""


@pytest.fixture
def site(tmp_path):
    return tmp_path / "site"


def episode(tmp_path: Path, name: str, text: str = POST, lang: str = "en") -> Path:
    source = tmp_path / "episodes" / name / f"{lang}.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(text)
    return source


def built(tmp_path: Path, site: Path):
    outputs, stray = build(tmp_path / "episodes", site / "posts", site / "images", "/blog/episodes", site / "plan.ts")
    return {path.relative_to(site).as_posix(): content for path, content in outputs.items()}, stray


def test_a_post_is_named_by_its_slug_and_takes_its_id_from_the_folder(tmp_path, site):
    episode(tmp_path, "02-example")
    outputs, _ = built(tmp_path, site)
    assert outputs["posts/en/example.svx"].decode() == '---\nid: example\ntitle: "What goes wrong"\n---\n\nThe intro.\n'


def test_an_id_in_the_frontmatter_is_refused(tmp_path, site):
    episode(tmp_path, "02-example", POST.replace("slug:", "id: example\nslug:"))
    with pytest.raises(EpisodeError, match="02-example/en.md: drop the id"):
        built(tmp_path, site)


def test_a_post_without_a_slug_is_refused(tmp_path, site):
    episode(tmp_path, "02-example", POST.replace("slug: example\n", ""))
    with pytest.raises(EpisodeError, match="needs a slug"):
        built(tmp_path, site)


def test_a_published_episode_without_a_question_is_refused(tmp_path, site):
    episode(tmp_path, "02-example", POST.replace("slug:", "publishedAt: 2026-10-01\nslug:"))
    with pytest.raises(EpisodeError, match="ends with a question"):
        built(tmp_path, site)


def test_the_post_ends_asking_the_reader_its_question(tmp_path, site):
    episode(tmp_path, "02-example", POST.replace("slug:", 'question: "Have you?"\nslug:'), lang="de")
    outputs, _ = built(tmp_path, site)
    assert outputs["posts/de/example.svx"].decode().endswith("The intro.\n\n**Have you?** Schreibt es mir in die Kommentare.\n")


def test_the_post_links_to_its_docs_chapter_and_says_whether_its_commands_are_tested(tmp_path, site, monkeypatch):
    chapters = tmp_path / "episodes" / "git-splice" / "test"
    chapters.mkdir(parents=True)
    (chapters / "README.md").write_text("# Tests\n\n```scrut\n$ true\n```\n")
    (chapters / "plain.md").write_text("# Plain\n")
    monkeypatch.setattr("post.GIT_SPLICE", tmp_path / "episodes" / "git-splice")
    episode(tmp_path, "02-tested", POST.replace("slug: example", "docs: ../git-splice/test/README.md\nslug: tested"))
    episode(tmp_path, "03-plain", POST.replace("slug: example", "docs: ../git-splice/test/plain.md\nslug: plain"))
    outputs, _ = built(tmp_path, site)
    assert outputs["posts/en/tested.svx"].decode().endswith(
        "\nMore in the git-splice docs, where every command is tested: [Tests](https://roschaefer.github.io/git-splice/test/).\n"
    )
    assert outputs["posts/en/plain.svx"].decode().endswith(
        "\nMore in the git-splice docs: [Plain](https://roschaefer.github.io/git-splice/test/plain/).\n"
    )


def test_docs_outside_git_splice_are_refused(tmp_path, site):
    episode(tmp_path, "02-example", POST.replace("slug:", "docs: ../README.md\nslug:"))
    (tmp_path / "episodes" / "README.md").write_text("# Episodes\n")
    with pytest.raises(EpisodeError, match="docs must be a chapter in git-splice/"):
        built(tmp_path, site)


def test_a_code_blocks_address_line_is_left_out_of_the_post(tmp_path, site):
    episode(tmp_path, "02-example", POST + "\n```console\n# example.org/docs\n$ git status\n```\n")
    outputs, _ = built(tmp_path, site)
    assert outputs["posts/en/example.svx"].decode().endswith("\n```console\n$ git status\n```\n")


def test_images_are_copied_and_their_paths_point_at_the_copies(tmp_path, site):
    source = episode(tmp_path, "02-example", POST + "\n![A diagram](diagram.svg)\n![Elsewhere](https://example.org/x.svg)\n")
    (source.parent / "diagram.svg").write_text("<svg/>")
    outputs, _ = built(tmp_path, site)
    assert outputs["images/diagram.svg"] == b"<svg/>"
    assert "\n![A diagram](/blog/episodes/diagram.svg)\n![Elsewhere](https://example.org/x.svg)\n" in outputs["posts/en/example.svx"].decode()


def test_two_images_with_one_name_are_refused(tmp_path, site):
    for name in ("02-one", "03-two"):
        source = episode(tmp_path, name, POST.replace("slug: example", f"slug: {name}") + "\n![A diagram](diagram.svg)\n")
        (source.parent / "diagram.svg").write_text(name)
    with pytest.raises(EpisodeError, match="share the name diagram.svg"):
        built(tmp_path, site)


def test_the_episodes_numbers_are_the_publication_plan(tmp_path, site):
    episode(tmp_path, "10-later", POST.replace("slug: example", "slug: later"))
    episode(tmp_path, "02-sooner", POST.replace("slug: example", "slug: sooner"))
    outputs, _ = built(tmp_path, site)
    assert outputs["plan.ts"].decode().startswith('export const publicationPlan: string[] = [\n\t"sooner",\n\t"later",\n];\n')


def test_stale_images_and_renamed_posts_are_removed_but_other_posts_stay(tmp_path, site):
    episode(tmp_path, "02-example")
    (site / "images").mkdir(parents=True)
    (site / "images" / "gone.svg").write_text("<svg/>")
    (site / "posts" / "en").mkdir(parents=True)
    (site / "posts" / "en" / "old-slug.svx").write_text("---\nid: example\n---\n")
    (site / "posts" / "en" / "by-hand.svx").write_text("---\nid: by-hand\n---\n")
    _, stray = built(tmp_path, site)
    assert sorted(path.name for path in stray) == ["gone.svg", "old-slug.svx"]
