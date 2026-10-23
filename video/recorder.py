"""Records my voiceovers, started and stopped with Enter.

manim-voiceover's recorder records while a key is held, which it reads
with pynput, and pynput doesn't see keys under Wayland. Enter reaches any
terminal.
"""

import wave
from pathlib import Path

import pyaudio
from manim_voiceover.helper import trim_silence, wav2mp3
from manim_voiceover.services.recorder import RecorderService
from manim_voiceover.services.recorder.utility import Recorder
from pydub import AudioSegment
from pydub.playback import play


class EnterRecorder(Recorder):
    def _record(self, path: str) -> None:
        self._trigger_set_device()
        self.frames = []
        input("Press Enter, wait a second, then speak.")
        stream = self._audio().open(
            format=self.format,
            channels=self._channels(),
            rate=self.rate,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=self.chunk,
            stream_callback=self.callback,
        )
        input("Recording. Press Enter when you're done.")
        stream.stop_stream()
        stream.close()

        wav_path = str(Path(path).with_suffix(".wav"))
        with wave.open(wav_path, "wb") as wav:
            wav.setnchannels(self._channels())
            wav.setsampwidth(self._audio().get_sample_size(self.format))
            wav.setframerate(self.rate)
            # Drops the last half second, the Enter key's click.
            wav.writeframes(b"".join(self.frames[: -int(self.rate * 0.5 / self.chunk)]))
        trim_silence(
            AudioSegment.from_wav(wav_path),
            silence_threshold=self.trim_silence_threshold,
            buffer_start=self.trim_buffer_start,
            buffer_end=self.trim_buffer_end,
        ).export(wav_path, format="wav")
        wav2mp3(wav_path)

    def record(self, path: str, message: str | None = None) -> None:
        if message is not None:
            print(message)
        self._record(path)
        while True:
            choice = input("[l]isten, [r]e-record or [a]ccept? ").strip().lower()
            if choice == "l":
                play(AudioSegment.from_file(path))
            elif choice == "r":
                if message is not None:
                    print(message)
                self._record(path)
            elif choice == "a":
                return


class EnterRecorderService(RecorderService):
    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.recorder.__class__ = EnterRecorder
