import subprocess
import logging
from pathlib import Path
from typing import Optional
from .config import Config

logger = logging.getLogger(__name__)


class AudioConverter:
    def __init__(self, config: Config):
        self.config = config

    def convert_mp3_to_wav(
        self,
        mp3_path: Optional[Path] = None,
        output_path: Optional[Path] = None,
    ) -> Path:
        if mp3_path is None:
            mp3_path = self.config.input_file
        if output_path is None:
            output_path = self.config.temp_dir / "audio.wav"

        logger.info(f"Converting {mp3_path} to {output_path}")

        cmd = [
            "ffmpeg",
            "-i", str(mp3_path),
            "-ar", str(self.config.sample_rate),
            "-ac", "1",
            "-acodec", "pcm_s16le",
            "-y",
            str(output_path),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            logger.info("Audio conversion completed")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr}")
            raise RuntimeError(f"Audio conversion failed: {e}") from e
        except FileNotFoundError:
            raise RuntimeError(
                "FFmpeg not found. Please install FFmpeg and ensure it's in PATH."
            )

    def get_audio_duration(self, wav_path: Optional[Path] = None) -> float:
        if wav_path is None:
            wav_path = self.config.temp_dir / "audio.wav"

        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(wav_path),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            return float(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError) as e:
            logger.error(f"Failed to get audio duration: {e}")
            return 0.0
