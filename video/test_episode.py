import json
from pathlib import Path

import pytest
from episode import FRAME_WIDTH, MIN_BLOCK_SECONDS, Block, append_new_take, drawing, framed, shown_code, shown_link, default_stroke_width, find_episode, parse, spoken, still_to_show

POST = """---
slug: example
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


def test_a_paragraph_ending_in_a_colon_plays_over_the_block_it_introduces(tmp_path):
    post = tmp_path / "example" / "en.md"
    post.parent.mkdir()
    post.write_text(POST.replace("Second paragraph.", "Second paragraph.\n\nThe diagram shows:"))
    code, image = parse(post)[2:]
    assert code.narration[-1] == "Second paragraph."
    assert image.narration == ["The diagram shows:", "Read over the diagram."]


def test_a_colon_introduces_only_the_next_block(tmp_path):
    post = tmp_path / "example" / "en.md"
    post.parent.mkdir()
    post.write_text(POST.replace("Read over the heading.", "Read over the heading.\n\nThe output:\n\nIt changed."))
    heading, code = parse(post)[1:3]
    assert heading.narration == ["Read over the heading.", "The output:", "It changed."]
    assert code.narration[0] == "First paragraph about the output. Still the first paragraph."


def test_a_block_introduced_by_a_colon_keeps_it_when_the_next_block_follows_directly(tmp_path):
    post = tmp_path / "example" / "en.md"
    post.parent.mkdir()
    post.write_text(POST.replace("Read over the heading.", "The output:").replace(
        "First paragraph about the output.\nStill the first paragraph.\n\nSecond paragraph.\n", ""))
    heading, code, image = parse(post)[1:]
    assert heading.narration == []
    assert code.narration == ["The output:"]
    assert image.narration == ["Read over the diagram."]


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
    monkeypatch.setattr("post.GIT_SPLICE", tmp_path / "git-splice")
    post = tmp_path / "episodes" / "02-example" / "en.md"
    post.parent.mkdir(parents=True)
    post.write_text(POST.replace("title:", "docs: ../../git-splice/test/chapter.md\ntitle:"))

    assert parse(post)[-1] == Block(
        "docs",
        "More in the git-splice docs\ngit subtree compared\nroschaefer.github.io/git-splice/test/chapter",
    )


def test_an_episode_with_a_docs_chapter_and_a_question_ends_on_one_slide_with_both(tmp_path, monkeypatch):
    chapter = tmp_path / "git-splice" / "test" / "chapter.md"
    chapter.parent.mkdir(parents=True)
    chapter.write_text("# `git subtree` compared\n")
    monkeypatch.setattr("post.GIT_SPLICE", tmp_path / "git-splice")
    post = tmp_path / "episodes" / "02-example" / "en.md"
    post.parent.mkdir(parents=True)
    post.write_text(POST.replace("title:", 'docs: ../../git-splice/test/chapter.md\nquestion: "Have you?"\ntitle:'))

    blocks = parse(post)
    assert blocks[-2].kind != "docs"
    assert blocks[-1] == Block(
        "closing",
        "Have you?\nWrite it in the comments below.\nMore in the git-splice docs\ngit subtree compared\nroschaefer.github.io/git-splice/test/chapter",
        ["Have you? Write it in the comments below."],
    )
    assert shown_link(blocks[-1]) == "https://roschaefer.github.io/git-splice/test/chapter"
    slide, corner = framed(blocks[-1])
    assert corner.get_top()[1] < slide.get_bottom()[1]


def test_a_diagrams_1px_lines_stay_visible():
    svg = '<rect x="1" stroke="#000000"/><rect stroke="#000000" stroke-width="2"/><rect stroke="none"/><path d="M 0 0" fill="#000"/>'
    assert default_stroke_width(svg) == (
        '<rect stroke-width="1" x="1" stroke="#000000"/><rect stroke="#000000" stroke-width="2"/><rect stroke="none"/><path d="M 0 0" fill="#000"/>'
    )


def test_a_take_is_listed_in_the_cache_once_however_often_the_video_renders(tmp_path):
    cache = tmp_path / "cache.json"
    take = {"input_text": "Hi.", "input_data": {"input_text": "Hi.", "service": "recorder"}, "original_audio": "hi.mp3"}
    append_new_take(cache, take)
    append_new_take(cache, take)
    assert [entry["original_audio"] for entry in json.loads(cache.read_text())] == ["hi.mp3"]


def test_the_docs_card_and_a_code_blocks_address_line_link_to_what_they_show():
    assert shown_link(Block("docs", "More\nChapter\nroschaefer.github.io/git-splice/x")) == "https://roschaefer.github.io/git-splice/x"
    assert shown_link(Block("code", "# example.org/docs\ngit clone x")) == "https://example.org/docs"


def test_blocks_without_an_address_for_viewers_have_no_link():
    assert shown_link(Block("code", "git clone https://git.example.com/lib.git")) is None
    assert shown_link(Block("code", "$ git status --short\n# M app/main.txt")) is None
    assert shown_link(Block("heading", "A heading")) is None


@pytest.mark.parametrize("line", ["$ git status", "$ git log --oneline -- vendor/lib/src/parse.txt"])
def test_a_code_block_keeps_its_font_size_short_or_long(line):
    block = Block("code", line)
    assert framed(block).width == pytest.approx(drawing(block).width)


def test_a_code_block_too_wide_for_the_frame_shrinks_to_fit(capsys):
    assert framed(Block("code", "x" * 200)).width <= FRAME_WIDTH
    assert "shorten its lines" in capsys.readouterr().err


def test_a_code_blocks_address_line_is_no_code_but_goes_below_it_by_the_qr_code():
    block = Block("code", "# roschaefer.github.io/git-splice/docs/sandbox\nnix develop -c just sandbox")
    assert shown_code(block) == "nix develop -c just sandbox"
    code, corner = framed(block)
    assert corner.get_top()[1] < code.get_bottom()[1]
    assert corner.get_right()[0] > code.get_right()[0]


def test_a_block_with_nothing_said_over_it_stays_on_screen_for_the_minimum():
    assert still_to_show(1) == MIN_BLOCK_SECONDS - 1
    assert MIN_BLOCK_SECONDS >= 3


def test_a_block_shown_long_enough_already_moves_on_at_once():
    assert still_to_show(MIN_BLOCK_SECONDS + 5) == 0
