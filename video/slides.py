"""Renders an episode's <lang>.md as presentation slides: a PDF with one
page per block of the video, as the video shows it. See ../README.md.

    slides.py <episode> <lang> [l|m|h|k]
"""

import sys
from pathlib import Path

from episode import EPISODES, find_episode, framed, parse
from manim import Scene, tempconfig
from PIL import Image

QUALITY = {"l": "low_quality", "m": "medium_quality", "h": "high_quality", "k": "fourk_quality"}


def slides(episode: Path, lang: str, quality: str = "h") -> Path:
    pages = []
    for number, block in enumerate(parse(episode / f"{lang}.md"), 1):

        class Slide(Scene):
            def construct(self) -> None:
                self.add(framed(block))

        settings = {
            "quality": QUALITY[quality],
            "save_last_frame": True,
            "write_to_movie": False,
            "media_dir": str(EPISODES / "media"),
            "output_file": f"{episode.name}-{lang}-{number:02}",
            "verbosity": "WARNING",
            "progress_bar": "none",
        }
        with tempconfig(settings):
            scene = Slide()
            scene.render()
            pages.append(Image.open(scene.renderer.file_writer.image_file_path).convert("RGB"))
    pdf = EPISODES / "media" / "slides" / f"{episode.name}-{lang}.pdf"
    pdf.parent.mkdir(parents=True, exist_ok=True)
    # 144 dpi makes a full HD page 13.33 by 7.5 inches, the size of a widescreen slide.
    pages[0].save(pdf, save_all=True, append_images=pages[1:], resolution=144 * pages[0].width / 1920)
    return pdf


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        raise SystemExit(__doc__)
    print(slides(find_episode(sys.argv[1]), sys.argv[2], *sys.argv[3:]))
