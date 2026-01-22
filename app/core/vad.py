import logging
import numpy as np
from pathlib import Path
from typing import List, Tuple
import torch
from scipy.io import wavfile
from .config import Config

logger = logging.getLogger(__name__)


class VADSegmenter:
    def __init__(self, config: Config):
        self.config = config
        self.model = None
        self._load_model()

    def _load_model(self):
        try:
            model, utils = torch.hub.load(
                repo_or_dir="snakers4/silero-vad",
                model="silero_vad",
                force_reload=False,
                onnx=False,
            )
            self.model = model
            (get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils
            self.get_speech_timestamps = get_speech_timestamps
            logger.info("Silero VAD model loaded")
        except Exception as e:
            logger.error(f"Failed to load VAD model: {e}")
            raise

    def segment_audio(
        self,
        wav_path: Path,
    ) -> List[Tuple[float, float]]:
        logger.info(f"Segmenting audio using VAD: {wav_path}")

        try:
            sample_rate, audio_data = wavfile.read(str(wav_path))

            # Convert to float32 normalized to [-1, 1]
            if audio_data.dtype == np.int16:
                audio = audio_data.astype(np.float32) / 32768.0
            elif audio_data.dtype == np.int32:
                audio = audio_data.astype(np.float32) / 2147483648.0
            else:
                audio = audio_data.astype(np.float32)

            # Handle stereo by taking first channel
            if len(audio.shape) > 1:
                audio = audio[:, 0]

            speech_timestamps = self.get_speech_timestamps(
                audio,
                self.model,
                threshold=self.config.vad_threshold,
                sampling_rate=self.config.sample_rate,
                min_speech_duration_ms=self.config.min_speech_duration_ms,
                min_silence_duration_ms=self.config.min_silence_duration_ms,
                speech_pad_ms=self.config.speech_pad_ms,
            )

            segments = self._merge_segments(speech_timestamps)

            logger.info(f"VAD completed: {len(segments)} segments found")
            return segments

        except Exception as e:
            logger.error(f"VAD segmentation failed: {e}")
            raise

    def _merge_segments(
        self,
        timestamps: List[dict],
    ) -> List[Tuple[float, float]]:
        if not timestamps:
            return []

        segments = []
        current_start = timestamps[0]["start"] / self.config.sample_rate
        current_end = timestamps[0]["end"] / self.config.sample_rate

        for ts in timestamps[1:]:
            start = ts["start"] / self.config.sample_rate
            end = ts["end"] / self.config.sample_rate

            if start - current_end < (self.config.max_segment_duration_ms / 1000.0):
                current_end = end
            else:
                segments.append((current_start, current_end))
                current_start = start
                current_end = end

        segments.append((current_start, current_end))

        return segments

    def segments_to_dict(self, segments: List[Tuple[float, float]]) -> List[dict]:
        return [
            {"start": start, "end": end}
            for start, end in segments
        ]
