# MP3 Dictation & Meeting Minutes Generator

오프라인 Windows 데스크톱 앱 - MP3 회의 녹음을 받아쓰기하고 회의록을 생성합니다.

## 기능

- 오프라인 STT (faster-whisper)
- VAD 기반 발화 구간 분할 (Silero VAD)
- 회의록 자동 생성
- 체크포인트 지원 (중단 후 재개 가능)
- CLI + GUI (PySide6)
- RTX 4090 가속 지원

## 설치

### 1. Python 3.10+ 설치

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. FFmpeg 설치

**Windows:**
1. [FFmpeg](https://ffmpeg.org/download.html) 다운로드
2. 압축 해제 후 `bin` 폴더를 PATH에 추가

**확인:**
```bash
ffmpeg -version
```

## 사용 방법

### CLI

```bash
python main.py --input meeting.mp3 --output output --model large-v3
```

**옵션:**
- `--input`: 입력 MP3 파일 (필수)
- `--output`: 출력 폴더 (기본: output)
- `--model`: 모델 크기 (large-v3, large-v2, medium, small, base)
- `--compute-type`: 연산 타입 (int8_float16, float16, float32, int8)
- `--language`: 언어 (ko, en, auto, ja, zh)
- `--device`: 장치 (cuda, cpu)
- `--workers`: 워커 수 (기본: 1)
- `--prompt`: Initial Prompt (용어 사전)
- `--meeting-title`: 회의명
- `--meeting-date`: 회의 일시
- `--attendees`: 참석자
- `--project`: 프로젝트명

### GUI

```bash
python app/ui/gui.py
```

## 출력 파일

### 1. transcript.json
```json
{
  "meeting_info": {
    "title": "프로젝트 회의",
    "date": "2026-01-22",
    "attendees": "김철수, 이영희",
    "project": "LIS 시스템 개발"
  },
  "segments": [
    {
      "start": 10.5,
      "end": 25.3,
      "text": "오늘은 EMR 연동 기능에 대해 논의하겠습니다.",
      "words": [...]
    }
  ]
}
```

### 2. transcript.md
```markdown
# 회의 녹음 전문 (Transcript)

**회의명**: 프로젝트 회의
**일시**: 2026-01-22
**참석자**: 김철수, 이영희

---

## [1] 00:00:10 - 00:00:25

오늘은 EMR 연동 기능에 대해 논의하겠습니다.
```

### 3. minutes.md
```markdown
# 회의록 (Meeting Minutes)

## 회의 개요

- **회의명**: 프로젝트 회의
- **일시**: 2026-01-22
- **참석자**: 김철수, 이영희
- **프로젝트**: LIS 시스템 개발

## 논의 내용

- EMR 연동 방식 검토 (근거: 00:00:10-00:00:25)
- LIS 인터페이스 설계 (근거: 00:01:30-00:02:10)

## 결정사항

- HL7 FHIR 방식 채택 (근거: 00:05:20-00:05:35)

## Action Items

1. FHIR API 구현 (근거: 00:10:15-00:10:40)
   - 담당자: 김철수
   - 기한: 2026-02-15

## 리스크/이슈

리스크/이슈 없음

## 추가 확인 필요 (Open Questions)

추가 확인 필요 없음
```

## 오프라인 모델 설정

### huggingface-cli 설치
```bash
pip install huggingface-cli
```

### 모델 사전 다운로드

```bash
# Whisper 모델
huggingface-cli download Systran/faster-whisper-large-v3 --local-dir models/whisper-large-v3

# Silero VAD
python -c "import torch; torch.hub.load('snakers4/silero-vad', model='silero_vad')"
```

### 모델 경로 지정

```bash
python main.py --input meeting.mp3 --model models/whisper-large-v3
```

## 빌드 (Windows exe)

### PyInstaller 설치

```bash
pip install pyinstaller
```

### 빌드 실행

```bash
pyinstaller --onefile --windowed \
  --name DictationApp \
  --icon assets/icon.ico \
  --add-data "app:app" \
  app/ui/gui.py
```

### 필요한 데이터 포함

FFmpeg와 모델 파일을 별도로 배포하거나 설치 가이드를 제공하세요.

## 트러블슈팅

### CUDA 오류
- CUDA 드라이버 설치 확인
- `--device cpu` 옵션으로 테스트

### FFmpeg 오류
- FFmpeg가 PATH에 포함되어 있는지 확인
- `ffmpeg -version` 실행해보세요

### 메모리 부족
- 모델 크기를 `medium` 또는 `small`로 변경
- `--compute-type int8` 사용

### VAD 오류
- 네트워크 연결 확인 (최초 1회만 필요)
- Silero VAD 모델을 로컬에 다운로드

## 성능

- 60분 MP3: RTX 4090에서 약 15-20분
- CPU만 사용 시: 약 2-3시간

## 라이선스

MIT License
