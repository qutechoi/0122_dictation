# MP3 음성 받아쓰기 및 회의록 자동 생성기

오프라인 환경에서 MP3 회의 녹음 파일을 텍스트로 변환하고 회의록을 자동 생성하는 도구입니다.

## 주요 기능

- **오프라인 음성 인식**: faster-whisper 기반 STT (인터넷 연결 불필요)
- **음성 구간 자동 감지**: Silero VAD로 발화 구간 분할
- **회의록 자동 생성**: 논의 내용, 결정사항, Action Items 자동 추출
- **체크포인트 지원**: 중단 후 재개 가능
- **GPU 가속**: CUDA 지원 (RTX 4090 등)
- **다양한 출력 형식**: JSON, Markdown, SRT 자막

## 설치

### 1. Python 3.10 이상 설치

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. FFmpeg 설치

**Windows:**
1. [FFmpeg 공식 사이트](https://ffmpeg.org/download.html)에서 다운로드
2. 압축 해제 후 `bin` 폴더를 시스템 PATH에 추가

**설치 확인:**
```bash
ffmpeg -version
```

## 사용법

### CLI (명령줄)

```bash
python main.py --input <MP3파일> [옵션]
```

### 필수 옵션

| 옵션 | 설명 |
|------|------|
| `--input` | 입력 MP3 파일 경로 |

### 선택 옵션

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--output` | `output` | 출력 폴더 |
| `--model` | `large-v3` | 모델 크기 (`large-v3`, `large-v2`, `medium`, `small`, `base`) |
| `--compute-type` | `int8_float16` | 연산 타입 (`int8_float16`, `float16`, `float32`, `int8`) |
| `--language` | `ko` | 언어 코드 (`ko`, `en`, `ja`, `zh`, `auto`) |
| `--device` | `cuda` | 장치 (`cuda`, `cpu`) |
| `--workers` | `1` | 워커 수 |
| `--prompt` | - | 전문 용어 힌트 (Initial Prompt) |

### 회의록 메타데이터

| 옵션 | 설명 |
|------|------|
| `--meeting-title` | 회의명 |
| `--meeting-date` | 회의 일시 |
| `--attendees` | 참석자 |
| `--project` | 프로젝트명 |

### 사용 예시

**기본 사용:**
```bash
python main.py --input meeting.mp3
```

**회의 정보 포함:**
```bash
python main.py --input meeting.mp3 \
  --output results \
  --meeting-title "주간 회의" \
  --meeting-date "2026-01-22" \
  --attendees "김철수, 이영희" \
  --project "신규 프로젝트"
```

**CPU만 사용 (GPU 없는 경우):**
```bash
python main.py --input meeting.mp3 --device cpu --model medium
```

**전문 용어 힌트:**
```bash
python main.py --input meeting.mp3 --prompt "EMR, LIS, FHIR, HL7, HbA1c"
```

### GUI 실행

```bash
python app/ui/gui.py
```

## 출력 파일

| 파일 | 용도 |
|------|------|
| `transcript.json` | 프로그램 연동용 (타임스탬프 포함) |
| `transcript.md` | 전문 읽기용 |
| `transcript.srt` | 영상 자막용 |
| `minutes.md` | 회의록 |

### 출력 예시

**transcript.md:**
```markdown
## [1] 00:00:10 - 00:00:25

오늘은 EMR 연동 기능에 대해 논의하겠습니다.
```

**minutes.md:**
```markdown
## 논의 내용

- EMR 연동 방식 검토 (근거: 00:00:10)

## 결정사항

- HL7 FHIR 방식 채택 (근거: 00:05:20)

## Action Items

1. FHIR API 구현 (근거: 00:10:15)
   - 담당자/기한: 미정
```

## 오프라인 모델 설정

인터넷 없이 사용하려면 모델을 미리 다운로드하세요.

### Whisper 모델 다운로드

```bash
pip install huggingface-cli
huggingface-cli download Systran/faster-whisper-large-v3 --local-dir models/whisper-large-v3
```

### Silero VAD 모델 다운로드

```bash
python -c "import torch; torch.hub.load('snakers4/silero-vad', model='silero_vad')"
```

### 로컬 모델 사용

```bash
python main.py --input meeting.mp3 --model models/whisper-large-v3
```

## 성능

| 환경 | 60분 MP3 처리 시간 |
|------|-------------------|
| RTX 4090 (CUDA) | 약 15-20분 |
| CPU만 사용 | 약 2-3시간 |

## 트러블슈팅

### CUDA 오류
- CUDA 드라이버 설치 확인
- `--device cpu` 옵션으로 테스트

### FFmpeg 오류
- FFmpeg가 PATH에 포함되어 있는지 확인
- `ffmpeg -version` 실행해서 확인

### 메모리 부족
- 모델 크기를 `medium` 또는 `small`로 변경
- `--compute-type int8` 사용

### VAD 오류
- 네트워크 연결 확인 (최초 1회 모델 다운로드 필요)
- Silero VAD 모델을 로컬에 미리 다운로드

## 라이선스

MIT License
