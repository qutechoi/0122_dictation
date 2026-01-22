import logging
import json
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class CheckpointManager:
    def __init__(self, checkpoint_path: Path):
        self.checkpoint_path = checkpoint_path

    def save(self, data: dict):
        with open(self.checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Checkpoint saved: {self.checkpoint_path}")

    def load(self) -> Optional[dict]:
        if not self.checkpoint_path.exists():
            return None

        try:
            with open(self.checkpoint_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Checkpoint loaded: {self.checkpoint_path}")
            return data
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}")
            return None

    def save_segments(
        self,
        done_segments: List[int],
        transcribed: List[Dict],
    ):
        data = {
            "done_segments": done_segments,
            "transcribed": transcribed,
        }
        self.save(data)

    def load_segments(self) -> Optional[dict]:
        return self.load()

    def delete(self):
        if self.checkpoint_path.exists():
            self.checkpoint_path.unlink()
            logger.info(f"Checkpoint deleted: {self.checkpoint_path}")
