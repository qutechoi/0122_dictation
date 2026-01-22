import unittest
from pathlib import Path
import json

from app.core.postprocess import PostProcessor
from app.core.config import Config


class TestSegmentMerge(unittest.TestCase):
    def setUp(self):
        self.config = Config(
            input_file="dummy.mp3",
            output_dir="test_output",
        )
        self.processor = PostProcessor(self.config)

    def test_merge_segments(self):
        segments = [
            {"start": 10.5, "end": 15.3, "text": " hello  world "},
            {"start": 20.2, "end": 25.8, "text": " test  message "},
        ]

        merged = self.processor.merge_segments(segments)

        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0]["text"], "hello world")
        self.assertEqual(merged[1]["text"], "test message")

    def test_normalize_text(self):
        text = " lis emr qc hba1c "
        normalized = self.processor.normalize_text(text)

        self.assertEqual(normalized, "LIS EMR QC HbA1c")

    def test_format_timestamp(self):
        timestamp = 3661.5
        formatted = self.processor._format_timestamp(timestamp)

        self.assertEqual(formatted, "01:01:01")

    def test_format_srt_timestamp(self):
        timestamp = 3661.5
        formatted = self.processor._format_srt_timestamp(timestamp)

        self.assertEqual(formatted, "01:01:01,500")


if __name__ == "__main__":
    unittest.main()
