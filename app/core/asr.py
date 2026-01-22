import logging
from pathlib import Path
from typing import List, Dict, Optional
import torch
from faster_whisper import WhisperModel
from .config import Config

logger = logging.getLogger(__name__)


class ASREngine:
    def __init__(self, config: Config):
        self.config = config
        self.model = None
        self._load_model()

    def _load_model(self):
        logger.info(f"Loading Whisper model: {self.config.model_name}")

        try:
            self.model = WhisperModel(
                model_size_or_path=self.config.get_model_path(),
                device=self.config.device,
                compute_type=self.config.compute_type,
            )
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise

    def transcribe_segment(
        self,
        audio_path: Path,
        start_sec: float,
        end_sec: float,
        offset_sec: float = 0.0,
    ) -> List[Dict]:
        logger.debug(f"Transcribing segment [{start_sec:.2f}-{end_sec:.2f}]")

        try:
            segments, info = self.model.transcribe(
                str(audio_path),
                beam_size=5,
                vad_filter=False,
                language=self.config.language if self.config.language != "auto" else None,
                condition_on_previous_text=False,
                word_timestamps=True,
                initial_prompt=self.config.initial_prompt,
                segments=[(start_sec, end_sec)],
            )

            results = []
            for segment in segments:
                results.append({
                    "start": offset_sec + segment.start,
                    "end": offset_sec + segment.end,
                    "text": segment.text.strip(),
                    "words": [
                        {
                            "start": offset_sec + word.start,
                            "end": offset_sec + word.end,
                            "word": word.word,
                            "probability": word.probability,
                        }
                        for word in segment.words
                    ] if hasattr(segment, "words") else [],
                })

            logger.debug(f"Segment transcribed: {len(results)} sub-segments")
            return results

        except Exception as e:
            logger.error(f"Failed to transcribe segment: {e}")
            return []

    def transcribe_all_segments(
        self,
        audio_path: Path,
        segments: List[Dict],
        progress_callback: Optional[callable] = None,
    ) -> List[Dict]:
        logger.info(f"Starting transcription for {len(segments)} segments")

        all_results = []
        total = len(segments)

        for idx, seg in enumerate(segments):
            if progress_callback:
                progress_callback(idx, total, f"Transcribing segment {idx + 1}/{total}")

            results = self.transcribe_segment(
                audio_path,
                seg["start"],
                seg["end"],
                offset_sec=seg["start"],
            )

            all_results.extend(results)

            logger.info(f"Segment {idx + 1}/{total} completed")

        logger.info(f"Transcription completed: {len(all_results)} total segments")
        return all_results
