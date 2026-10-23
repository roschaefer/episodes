from pathlib import Path

import pytest
from episode import Block, default_stroke_width, find_episode, parse, spoken

POST = """---
slug: example
id: example
title: "What goes wrong"
---

The intro, read over the title card.

## A heading

Read over the heading.

```console
$ git status --short
 M app/main.txt
```

First paragraph about the output.
Still the first paragraph.

Second paragraph.

![A diagram](../diagram.svg)

Read over the diagram.
"""


def blocks(tmp_path: Path):
    post = tmp_path / "example" / "en.md"
    post.parent.mkdir()
    post.write_text(POST)
    return parse(post)


def test_every_heading_diagram_and_code_block_starts_a_block(tmp_path):
    assert [block.kind for block in blocks(tmp_path)] == ["title", "heading", "code", "image"]


def test_the_intro_plays_over_a_title_card_with_the_post_title(tmp_path):
    title = blocks(tmp_path)[0]
    assert title.content == "What goes wrong"
    assert title.narration == ["The intro, read over the title card."]


def test_each_paragraph_up_to_the_next_block_is_one_voiceover(tmp_path):
    code = blocks(tmp_path)[2]
    assert code.content == "$ git status --short\n M app/main.txt"
    assert code.narration == [
        "First paragraph about the output. Still the first paragraph.",
        "Second paragraph.",
    ]


def test_diagram_paths_are_relative_to_the_post(tmp_path):
    assert blocks(tmp_path)[3].content == str(tmp_path / "diagram.svg")


def test_the_video_ends_asking_the_viewer_its_question(tmp_path):
    post = tmp_path / "example" / "en.md"
    post.parent.mkdir()
    post.write_text(POST.replace('title: "What goes wrong"\n', 'title: "What goes wrong"\nquestion: "Have you?"\n'))
    last = parse(post)[-1]
    assert (last.kind, last.content) == ("question", "Have you?\nWrite it in the comments below.")
    assert last.narration == ["Have you? Write it in the comments below."]


def test_the_german_video_asks_in_german(tmp_path):
    post = tmp_path / "example" / "de.md"
    post.parent.mkdir()
    post.write_text(POST.replace('title: "What goes wrong"\n', 'title: "Was schiefgeht"\nquestion: "Habt ihr?"\n'))
    blocks = parse(post)
    assert blocks[0].content == "Was schiefgeht"
    assert blocks[-1].narration == ["Habt ihr? Schreibt es mir in die Kommentare."]


def test_narration_is_read_without_markdown_syntax():
    assert spoken("- `git log` is *empty*, see [the docs](https://example.com)") == (
        "git log is empty, see the docs"
    )


@pytest.mark.parametrize("name", ["01-submodule-problems", "submodule-problems", "01", "1"])
def test_an_episode_is_found_by_folder_name_id_or_number(tmp_path, name):
    for folder in ["01-submodule-problems", "02-subtree-problems"]:
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "en.md").write_text(POST)
    assert find_episode(name, tmp_path) == tmp_path / "01-submodule-problems"


def test_an_unknown_episode_lists_the_known_ones(tmp_path):
    (tmp_path / "01-submodule-problems").mkdir()
    (tmp_path / "01-submodule-problems" / "en.md").write_text(POST)
    with pytest.raises(SystemExit, match="Episodes: 01-submodule-problems"):
        find_episode("submodule-preview", tmp_path)


def test_an_episode_with_a_docs_chapter_ends_on_a_link_to_it(tmp_path, monkeypatch):
    chapter = tmp_path / "git-splice" / "test" / "chapter.md"
    chapter.parent.mkdir(parents=True)
    chapter.write_text("# `git subtree` compared\n")
    monkeypatch.setattr("episode.GIT_SPLICE", tmp_path / "git-splice")
    post = tmp_path / "episodes" / "02-example" / "en.md"
    post.parent.mkdir(parents=True)
    post.write_text(POST.replace("title:", "docs: ../../git-splice/test/chapter.md\ntitle:"))

    assert parse(post)[-1] == Block(
        "docs",
        "More in the git-splice docs\ngit subtree compared\nroschaefer.github.io/git-splice/test/chapter",
    )


def test_a_diagrams_1px_lines_stay_visible():
    svg = '<rect x="1" stroke="#000000"/><rect stroke="#000000" stroke-width="2"/><rect stroke="none"/><path d="M 0 0" fill="#000"/>'
    assert default_stroke_width(svg) == (
        '<rect stroke-width="1" x="1" stroke="#000000"/><rect stroke="#000000" stroke-width="2"/><rect stroke="none"/><path d="M 0 0" fill="#000"/>'
    )
