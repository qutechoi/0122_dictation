from dataclasses import dataclass, field
from typing import Optional, List, Union
from pathlib import Path


@dataclass
class Config:
    input_file: Union[str, Path]
    output_dir: Union[str, Path] = "output"
    model_name: str = "large-v3"
    compute_type: str = "int8_float16"
    language: str = "ko"
    device: str = "cuda"
    num_workers: int = 1

    initial_prompt: Optional[str] = None

    meeting_title: Optional[str] = None
    meeting_date: Optional[str] = None
    attendees: Optional[str] = None
    project_name: Optional[str] = None

    vad_threshold: float = 0.5
    min_speech_duration_ms: int = 250
    min_silence_duration_ms: int = 2000
    max_segment_duration_ms: int = 30000
    speech_pad_ms: int = 30

    sample_rate: int = 16000
    temp_dir: Union[str, Path] = "temp"

    checkpoint_file: Union[str, Path] = "checkpoint.json"

    def __post_init__(self):
        self.output_dir = Path(self.output_dir)
        self.input_file = Path(self.input_file)
        self.temp_dir = Path(self.temp_dir)
        self.checkpoint_file = self.output_dir / self.checkpoint_file

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def get_model_path(self) -> Optional[str]:
        model_map = {
            "large-v3": "Systran/faster-whisper-large-v3",
            "large-v2": "Systran/faster-whisper-large-v2",
            "medium": "Systran/faster-whisper-medium",
            "small": "Systran/faster-whisper-small",
            "base": "Systran/faster-whisper-base",
        }
        return model_map.get(self.model_name, self.model_name)
