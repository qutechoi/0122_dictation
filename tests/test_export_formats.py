import unittest
import json
from pathlib import Path
import tempfile
import shutil

from app.core.postprocess import PostProcessor
from app.core.minutes import MinutesGenerator
from app.core.config import Config


class TestExportFormats(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.config = Config(
            input_file="dummy.mp3",
            output_dir=str(self.test_dir),
        )

        self.processor = PostProcessor(self.config)
        self.minutes_generator = MinutesGenerator(self.config)

        self.sample_segments = [
            {
                "start": 10.5,
                "end": 15.3,
                "text": "오늘은 EMR 연동 기능에 대해 논의하겠습니다.",
                "words": []
            },
            {
                "start": 90.2,
                "end": 95.8,
                "text": "FHIR 방식으로 결정했습니다. 김철수 님이 구현을 맡습니다.",
                "words": []
            },
        ]

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_export_json(self):
        json_path = self.test_dir / "test.json"
        self.processor.export_json(self.sample_segments, json_path)

        self.assertTrue(json_path.exists())

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIn("meeting_info", data)
        self.assertIn("segments", data)
        self.assertEqual(len(data["segments"]), 2)

    def test_export_markdown(self):
        md_path = self.test_dir / "test.md"
        self.processor.export_markdown(self.sample_segments, md_path)

        self.assertTrue(md_path.exists())

        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("회의 녹음 전문", content)
        self.assertIn("00:00:10 - 00:00:15", content)
        self.assertIn("오늘은 EMR 연동 기능에 대해 논의하겠습니다.", content)

    def test_export_srt(self):
        srt_path = self.test_dir / "test.srt"
        self.processor.export_srt(self.sample_segments, srt_path)

        self.assertTrue(srt_path.exists())

        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("00:00:10,500", content)
        self.assertIn("오늘은 EMR 연동 기능에 대해 논의하겠습니다.", content)

    def test_generate_minutes(self):
        minutes_path = self.test_dir / "minutes.md"
        self.minutes_generator.generate_minutes(self.sample_segments, minutes_path)

        self.assertTrue(minutes_path.exists())

        with open(minutes_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("회의록 (Meeting Minutes)", content)
        self.assertIn("논의 내용", content)
        self.assertIn("결정사항", content)
        self.assertIn("Action Items", content)


if __name__ == "__main__":
    unittest.main()
