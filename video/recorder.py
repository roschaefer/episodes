"""Records my voiceovers with PipeWire, started and stopped with Enter.

manim-voiceover's recorder records while a key is held, which it reads
with pynput, and pynput doesn't see keys under Wayland. It also records
and plays through the dev shell's ALSA, which knows nothing of PipeWire:
it sees only raw devices, records quietly, and plays where I can't hear.
pw-record and pw-play use the system's default microphone and speakers.
"""

import signal
import subprocess
import tempfile
from pathlib import Path

from manim_voiceover.helper import msg_box, remove_bookmarks, trim_silence, wav2mp3
from manim_voiceover.services.base import SpeechService
from pydub import AudioSegment

RATE = 48000


def default_microphone() -> str:
    inspect = subprocess.run(
        ["wpctl", "inspect", "@DEFAULT_AUDIO_SOURCE@"], capture_output=True, text=True
    ).stdout
    for line in inspect.splitlines():
        if "node.description" in line:
            return line.split("=", 1)[1].strip().strip('"')
    return "the default microphone"


def record(path: Path) -> None:
    input(f"Press Enter, wait a second, then speak. (Recording from {default_microphone()})")
    wav = path.with_suffix(".wav")
    recording = subprocess.Popen(["pw-record", "--rate", str(RATE), "--channels", "1", str(wav)])
    input("Recording. Press Enter when you're done.")
    recording.send_signal(signal.SIGINT)
    recording.wait()
    # Drops the last half second, the Enter key's click.
    take = trim_silence(AudioSegment.from_wav(wav)[:-500], silence_threshold=-40.0, buffer_start=200, buffer_end=200)
    take.export(wav, format="wav")
    wav2mp3(wav)


def play(path: Path) -> None:
    with tempfile.NamedTemporaryFile(suffix=".wav") as wav:
        AudioSegment.from_file(path).export(wav.name, format="wav")
        subprocess.run(["pw-play", wav.name])


class PipeWireRecorder(SpeechService):
    def generate_from_text(self, text: str, cache_dir=None, path=None, **kwargs):
        input_text = remove_bookmarks(text)
        cache_dir = Path(cache_dir or self.cache_dir)
        input_data = {"input_text": input_text, "config": {"rate": RATE, "channels": 1}, "service": "recorder"}
        cached = self.get_cached_result(input_data, cache_dir)
        if cached is not None:
            return cached
        audio = path or self.get_audio_basename(input_data) + ".mp3"
        box = msg_box("Voiceover:\n\n" + input_text)
        print(box)
        record(cache_dir / audio)
        while True:
            choice = input("[l]isten, [r]e-record or [a]ccept? ").strip().lower()
            if choice == "l":
                play(cache_dir / audio)
            elif choice == "r":
                print(box)
                record(cache_dir / audio)
            elif choice == "a":
                return {"input_text": text, "input_data": input_data, "original_audio": audio}
