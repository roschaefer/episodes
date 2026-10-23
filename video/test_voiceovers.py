import json

import pytest
from voiceovers import check, prune, retake, status

POST = """---
slug: example
id: example
title: "Example"
---

First paragraph.

Second paragraph.
"""


@pytest.fixture
def episode(tmp_path):
    episode = tmp_path / "01-example"
    (episode / "voiceovers" / "en").mkdir(parents=True)
    (episode / "en.md").write_text(POST)
    return episode


def record(episode, *texts, lang="en"):
    voiceovers = episode / "voiceovers" / lang
    voiceovers.mkdir(parents=True, exist_ok=True)
    entries = []
    for index, text in enumerate(texts):
        (voiceovers / f"take-{index}.mp3").write_text("audio")
        entries.append({"input_data": {"input_text": text, "service": "recorder"}, "original_audio": f"take-{index}.mp3", "final_audio": f"take-{index}.mp3"})
    (voiceovers / "cache.json").write_text(json.dumps(entries))


def recorded(episode, lang="en"):
    return [take["input_data"]["input_text"] for take in json.loads((episode / "voiceovers" / lang / "cache.json").read_text())]


def test_status_numbers_the_paragraphs_and_marks_the_recorded_ones(episode, capsys):
    record(episode, "Second paragraph.")
    status(episode, "en")
    out = capsys.readouterr().out
    assert "  1  ·  First paragraph." in out
    assert "  2  ✓  Second paragraph." in out
    assert "1 of 2 paragraphs recorded." in out


def test_a_retake_discards_the_take_and_its_audio(episode):
    record(episode, "First paragraph.", "Second paragraph.")
    retake(episode, "en", [1])
    assert recorded(episode) == ["Second paragraph."]
    assert not (episode / "voiceovers" / "en" / "take-0.mp3").exists()
    assert (episode / "voiceovers" / "en" / "take-1.mp3").exists()


def test_a_retake_of_a_paragraph_that_does_not_exist_changes_nothing(episode):
    record(episode, "First paragraph.")
    with pytest.raises(SystemExit, match="No paragraph 3"):
        retake(episode, "en", [3])
    assert recorded(episode) == ["First paragraph."]


def test_check_fails_on_takes_of_text_the_script_no_longer_has(episode, capsys):
    record(episode, "First paragraph.", "A paragraph I since rewrote.")
    with pytest.raises(SystemExit):
        check(episode.parent)
    assert "A paragraph I since rewrote." in capsys.readouterr().out


def test_check_fails_on_audio_no_take_refers_to(episode):
    record(episode, "First paragraph.")
    (episode / "voiceovers" / "en" / "stray.mp3").write_text("audio")
    with pytest.raises(SystemExit):
        check(episode.parent)


def test_check_ignores_the_generated_voices_which_are_not_in_git(episode):
    record(episode, "First paragraph.")
    (episode / "voiceovers" / "en" / "piper").mkdir()
    (episode / "voiceovers" / "en" / "piper" / "old.wav").write_text("audio")
    check(episode.parent)


def test_prune_keeps_the_takes_the_script_still_has(episode):
    record(episode, "First paragraph.", "A paragraph I since rewrote.")
    (episode / "voiceovers" / "en" / "stray.mp3").write_text("audio")
    prune(episode)
    assert recorded(episode) == ["First paragraph."]
    assert sorted(path.name for path in (episode / "voiceovers" / "en").iterdir()) == ["cache.json", "take-0.mp3"]
    check(episode.parent)


def test_each_language_has_its_own_takes(episode, capsys):
    (episode / "de.md").write_text(POST.replace("First paragraph.", "Erster Absatz."))
    record(episode, "First paragraph.")
    record(episode, "Erster Absatz.", lang="de")
    check(episode.parent)
    status(episode, "de")
    assert "  1  ✓  Erster Absatz." in capsys.readouterr().out
    retake(episode, "de", [1])
    assert recorded(episode) == ["First paragraph."]


def test_check_reports_the_language_of_a_stale_take(episode, capsys):
    (episode / "de.md").write_text(POST)
    record(episode, "Ein Absatz, den ich umgeschrieben habe.", lang="de")
    with pytest.raises(SystemExit):
        check(episode.parent)
    assert "de: Ein Absatz, den ich umgeschrieben habe." in capsys.readouterr().out
