import logging
import re
from typing import List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class MinutesGenerator:
    def __init__(self, config):
        self.config = config

        self.action_patterns = [
            r'(?:할|해야|할 것|해줘|해주세요|부탁드립니다|요청드립니다)',
            r'(?:assign|assigned|assigns|will do|should do|please|request)',
        ]

        self.decision_patterns = [
            r'(?:결정|확정|선정|선정하|채택|채택하|최종)',
            r'(?:decided|determine|finalize|select|adopt)',
        ]

        self.issue_patterns = [
            r'(?:문제|이슈|리스크|우려|걱정|문제점|오류|버그|에러)',
            r'(?:issue|risk|problem|concern|worry|bug|error)',
        ]

    def generate_minutes(
        self,
        segments: List[Dict],
        output_path: Path,
    ):
        logger.info("Generating meeting minutes")

        full_text = " ".join([seg["text"] for seg in segments])

        discussions = self._extract_discussions(segments)
        decisions = self._extract_decisions(segments)
        action_items = self._extract_action_items(segments)
        issues = self._extract_issues(segments)
        open_questions = self._extract_open_questions(segments)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# 회의록 (Meeting Minutes)\n\n")

            f.write("## 회의 개요\n\n")
            if self.config.meeting_title:
                f.write(f"- **회의명**: {self.config.meeting_title}\n")
            if self.config.meeting_date:
                f.write(f"- **일시**: {self.config.meeting_date}\n")
            if self.config.attendees:
                f.write(f"- **참석자**: {self.config.attendees}\n")
            if self.config.project_name:
                f.write(f"- **프로젝트**: {self.config.project_name}\n")
            f.write("\n")

            f.write("## 논의 내용\n\n")
            if discussions:
                for discussion in discussions:
                    f.write(f"- {discussion['text']}")
                    if discussion.get("timestamp"):
                        f.write(f" (근거: {discussion['timestamp']})")
                    f.write("\n")
            else:
                f.write("논의 내용 없음\n")
            f.write("\n")

            f.write("## 결정사항\n\n")
            if decisions:
                for decision in decisions:
                    f.write(f"- {decision['text']}")
                    if decision.get("timestamp"):
                        f.write(f" (근거: {decision['timestamp']})")
                    f.write("\n")
            else:
                f.write("결정사항 없음\n")
            f.write("\n")

            f.write("## Action Items\n\n")
            if action_items:
                for idx, item in enumerate(action_items, 1):
                    f.write(f"{idx}. {item['text']}")
                    if item.get("timestamp"):
                        f.write(f" (근거: {item['timestamp']})")
                    f.write("\n")
                    if item.get("assignee"):
                        f.write(f"   - 담당자: {item['assignee']}\n")
                    if item.get("deadline"):
                        f.write(f"   - 기한: {item['deadline']}\n")
                    if not item.get("assignee") and not item.get("deadline"):
                        f.write("   - 담당자/기한: 미정\n")
                    f.write("\n")
            else:
                f.write("Action Items 없음\n")
            f.write("\n")

            f.write("## 리스크/이슈\n\n")
            if issues:
                for issue in issues:
                    f.write(f"- {issue['text']}")
                    if issue.get("timestamp"):
                        f.write(f" (근거: {issue['timestamp']})")
                    f.write("\n")
            else:
                f.write("리스크/이슈 없음\n")
            f.write("\n")

            f.write("## 추가 확인 필요 (Open Questions)\n\n")
            if open_questions:
                for question in open_questions:
                    f.write(f"- {question['text']}")
                    if question.get("timestamp"):
                        f.write(f" (근거: {question['timestamp']})")
                    f.write("\n")
            else:
                f.write("추가 확인 필요 없음\n"
                )
            f.write("\n")

        logger.info(f"Minutes generated: {output_path}")

    def _extract_discussions(
        self,
        segments: List[Dict],
        max_items: int = 10,
    ) -> List[Dict]:
        discussions = []

        for seg in segments:
            text = seg["text"].strip()
            if len(text) > 30:
                discussions.append({
                    "text": text,
                    "timestamp": self._format_timestamp(seg["start"]),
                })
                if len(discussions) >= max_items:
                    break

        return discussions

    def _extract_decisions(
        self,
        segments: List[Dict],
    ) -> List[Dict]:
        decisions = []

        combined_pattern = "|".join(self.decision_patterns)

        for seg in segments:
            text = seg["text"].strip()
            if re.search(combined_pattern, text, re.IGNORECASE):
                decisions.append({
                    "text": text,
                    "timestamp": self._format_timestamp(seg["start"]),
                })

        return decisions

    def _extract_action_items(
        self,
        segments: List[Dict],
    ) -> List[Dict]:
        action_items = []

        combined_pattern = "|".join(self.action_patterns)

        for seg in segments:
            text = seg["text"].strip()
            if re.search(combined_pattern, text, re.IGNORECASE):
                action_items.append({
                    "text": text,
                    "timestamp": self._format_timestamp(seg["start"]),
                    "assignee": self._extract_assignee(text),
                    "deadline": self._extract_deadline(text),
                })

        return action_items

    def _extract_issues(
        self,
        segments: List[Dict],
    ) -> List[Dict]:
        issues = []

        combined_pattern = "|".join(self.issue_patterns)

        for seg in segments:
            text = seg["text"].strip()
            if re.search(combined_pattern, text, re.IGNORECASE):
                issues.append({
                    "text": text,
                    "timestamp": self._format_timestamp(seg["start"]),
                })

        return issues

    def _extract_open_questions(
        self,
        segments: List[Dict],
    ) -> List[Dict]:
        questions = []

        for seg in segments:
            text = seg["text"].strip()
            if "?" in text or "물어봐" in text or "확인" in text:
                questions.append({
                    "text": text,
                    "timestamp": self._format_timestamp(seg["start"]),
                })

        return questions[:5]

    def _extract_assignee(self, text: str) -> str:
        names = re.findall(
            r'(?:담당자|by|from|with)\s*[:is]*\s*([가-힣A-Za-z]+(?:\s+[가-힣A-Za-z]+)?)',
            text,
            re.IGNORECASE
        )
        return names[0] if names else None

    def _extract_deadline(self, text: str) -> str:
        deadlines = re.findall(
            r'(?:기한|deadline|by|until|까지)\s*[:is]*\s*(\d{1,2}(?:월|월\s*\d{1,2}일|/|\.).*?)(?:까지|까지|$)',
            text,
            re.IGNORECASE
        )
        return deadlines[0] if deadlines else None

    def _format_timestamp(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
