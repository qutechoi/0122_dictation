import logging
import sys
import argparse
import time
from pathlib import Path

from app.core.config import Config
from app.core.audio import AudioConverter
from app.core.vad import VADSegmenter
from app.core.asr import ASREngine
from app.core.postprocess import PostProcessor
from app.core.minutes import MinutesGenerator
from app.core.io import CheckpointManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)


class DictationPipeline:
    def __init__(self, config: Config):
        self.config = config
        self.audio_converter = AudioConverter(config)
        self.vad_segmenter = VADSegmenter(config)
        self.asr_engine = ASREngine(config)
        self.post_processor = PostProcessor(config)
        self.minutes_generator = MinutesGenerator(config)
        self.checkpoint_manager = CheckpointManager(config.checkpoint_file)

    def progress_callback(self, current: int, total: int, message: str):
        progress = (current / total) * 100
        logger.info(f"[{progress:.1f}%] {message}")

    def run(self) -> bool:
        start_time = time.time()
        logger.info("=" * 50)
        logger.info("Starting dictation pipeline")
        logger.info("=" * 50)

        try:
            wav_path = self._convert_audio()
            segments = self._segment_audio(wav_path)
            transcribed = self._transcribe_segments(wav_path, segments)
            self._post_process_and_export(transcribed)

            elapsed = time.time() - start_time
            logger.info("=" * 50)
            logger.info(f"Pipeline completed in {elapsed:.1f} seconds")
            logger.info("=" * 50)

            self.checkpoint_manager.delete()
            return True

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            return False

    def _convert_audio(self) -> Path:
        logger.info("Step 1/4: Converting MP3 to WAV")
        wav_path = self.audio_converter.convert_mp3_to_wav()

        duration = self.audio_converter.get_audio_duration(wav_path)
        logger.info(f"Audio duration: {duration / 60:.1f} minutes")

        return wav_path

    def _segment_audio(self, wav_path: Path) -> list:
        logger.info("Step 2/4: VAD segmentation")
        segments = self.vad_segmenter.segment_audio(wav_path)

        logger.info(f"Found {len(segments)} speech segments")

        total_speech = sum(end - start for start, end in segments)
        logger.info(f"Total speech duration: {total_speech / 60:.1f} minutes")

        segments_dict = self.vad_segmenter.segments_to_dict(segments)

        return segments_dict

    def _transcribe_segments(
        self,
        wav_path: Path,
        segments: list,
    ) -> list:
        logger.info("Step 3/4: Speech-to-Text")

        checkpoint_data = self.checkpoint_manager.load_segments()

        done_segments = []
        transcribed = []

        if checkpoint_data:
            done_segments = checkpoint_data.get("done_segments", [])
            transcribed = checkpoint_data.get("transcribed", [])
            logger.info(f"Resuming from checkpoint: {len(done_segments)}/{len(segments)} segments done")

        total_segments = len(segments)

        for idx, segment in enumerate(segments):
            if idx in done_segments:
                continue

            self.progress_callback(
                idx,
                total_segments,
                f"Transcribing segment {idx + 1}/{total_segments}"
            )

            results = self.asr_engine.transcribe_segment(
                wav_path,
                segment["start"],
                segment["end"],
                offset_sec=segment["start"],
            )

            transcribed.extend(results)
            done_segments.append(idx)

            if idx % 5 == 0 or idx == total_segments - 1:
                self.checkpoint_manager.save_segments(done_segments, transcribed)

        return transcribed

    def _post_process_and_export(self, transcribed: list):
        logger.info("Step 4/4: Post-processing and export")

        merged = self.post_processor.merge_segments(transcribed)

        json_path = self.config.output_dir / "transcript.json"
        self.post_processor.export_json(merged, json_path)

        md_path = self.config.output_dir / "transcript.md"
        self.post_processor.export_markdown(merged, md_path)

        srt_path = self.config.output_dir / "transcript.srt"
        self.post_processor.export_srt(merged, srt_path)

        minutes_path = self.config.output_dir / "minutes.md"
        self.minutes_generator.generate_minutes(merged, minutes_path)

        logger.info(f"Output files saved to: {self.config.output_dir}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Offline MP3 Dictation & Meeting Minutes Generator"
    )

    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Input MP3 file path"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="Output directory (default: output)"
    )

    parser.add_argument(
        "--model",
        type=str,
        default="large-v3",
        choices=["large-v3", "large-v2", "medium", "small", "base"],
        help="Whisper model size (default: large-v3)"
    )

    parser.add_argument(
        "--compute-type",
        type=str,
        default="int8_float16",
        choices=["int8_float16", "float16", "float32", "int8"],
        help="Compute type for Whisper model (default: int8_float16)"
    )

    parser.add_argument(
        "--language",
        type=str,
        default="ko",
        help="Language code (default: ko)"
    )

    parser.add_argument(
        "--device",
        type=str,
        default="cuda",
        choices=["cuda", "cpu"],
        help="Device to use (default: cuda)"
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of workers (default: 1)"
    )

    parser.add_argument(
        "--prompt",
        type=str,
        help="Initial prompt for the model (optional)"
    )

    parser.add_argument(
        "--meeting-title",
        type=str,
        help="Meeting title (optional)"
    )

    parser.add_argument(
        "--meeting-date",
        type=str,
        help="Meeting date (optional)"
    )

    parser.add_argument(
        "--attendees",
        type=str,
        help="Attendees (optional)"
    )

    parser.add_argument(
        "--project",
        type=str,
        help="Project name (optional)"
    )

    return parser.parse_args()


def main():
    args = parse_args()

    config = Config(
        input_file=args.input,
        output_dir=args.output,
        model_name=args.model,
        compute_type=args.compute_type,
        language=args.language,
        device=args.device,
        num_workers=args.workers,
        initial_prompt=args.prompt,
        meeting_title=args.meeting_title,
        meeting_date=args.meeting_date,
        attendees=args.attendees,
        project_name=args.project,
    )

    pipeline = DictationPipeline(config)
    success = pipeline.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
