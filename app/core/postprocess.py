import logging
import re
from typing import List, Dict, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class PostProcessor:
    def __init__(self, config):
        self.config = config
        self.term_dict = {
            "lis": "LIS",
            "emr": "EMR",
            "qc": "QC",
            "hba1c": "HbA1c",
            "ast": "AST",
            "alt": "ALT",
            "pcr": "PCR",
            "maldi-tof": "MALDI-TOF",
        }

    def normalize_text(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        for term, normalized in self.term_dict.items():
            pattern = r'\b' + re.escape(term) + r'\b'
            text = re.sub(pattern, normalized, text, flags=re.IGNORECASE)

        return text

    def merge_segments(
        self,
        transcribed_segments: List[Dict],
    ) -> List[Dict]:
        logger.info(f"Merging {len(transcribed_segments)} segments")

        merged = []
        for seg in transcribed_segments:
            seg["text"] = self.normalize_text(seg["text"])
            merged.append(seg)

        merged.sort(key=lambda x: x["start"])

        logger.info(f"Merged to {len(merged)} segments")
        return merged

    def export_json(
        self,
        segments: List[Dict],
        output_path: Path,
    ):
        data = {
            "meeting_info": {
                "title": self.config.meeting_title,
                "date": self.config.meeting_date,
                "attendees": self.config.attendees,
                "project": self.config.project_name,
            },
            "segments": segments,
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Exported transcript to JSON: {output_path}")

    def export_markdown(
        self,
        segments: List[Dict],
        output_path: Path,
    ):
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# 회의 녹음 전문 (Transcript)\n\n")

            if self.config.meeting_title:
                f.write(f"**회의명**: {self.config.meeting_title}\n")
            if self.config.meeting_date:
                f.write(f"**일시**: {self.config.meeting_date}\n")
            if self.config.attendees:
                f.write(f"**참석자**: {self.config.attendees}\n")
            f.write("\n---\n\n")

            for idx, seg in enumerate(segments, 1):
                start_time = self._format_timestamp(seg["start"])
                end_time = self._format_timestamp(seg["end"])

                f.write(f"## [{idx}] {start_time} - {end_time}\n\n")
                f.write(f"{seg['text']}\n\n")

        logger.info(f"Exported transcript to Markdown: {output_path}")

    def _format_timestamp(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def export_srt(
        self,
        segments: List[Dict],
        output_path: Path,
    ):
        with open(output_path, 'w', encoding='utf-8') as f:
            for idx, seg in enumerate(segments, 1):
                start_time = self._format_srt_timestamp(seg["start"])
                end_time = self._format_srt_timestamp(seg["end"])

                f.write(f"{idx}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{seg['text']}\n\n")

        logger.info(f"Exported transcript to SRT: {output_path}")

    def _format_srt_timestamp(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
