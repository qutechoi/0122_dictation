# 오프라인 모델 설정 가이드

## 개요

이 가이드는 네트워크 연결 없이 모델을 사용하기 위한 사전 설정 방법을 설명합니다.

## 1. Whisper 모델 다운로드

### 1.1 huggingface-cli 설치

```bash
pip install huggingface-hub
```

### 1.2 모델 다운로드

```bash
# Large v3 (권장)
huggingface-cli download Systran/faster-whisper-large-v3 --local-dir models/whisper-large-v3

# Large v2
huggingface-cli download Systran/faster-whisper-large-v2 --local-dir models/whisper-large-v2

# Medium
huggingface-cli download Systran/faster-whisper-medium --local-dir models/whisper-medium

# Small
huggingface-cli download Systran/faster-whisper-small --local-dir models/whisper-small

# Base
huggingface-cli download Systran/faster-whisper-base --local-dir models/whisper-base
```

### 1.3 디렉토리 구조

```
models/
├── whisper-large-v3/
│   ├── model.bin
│   ├── config.json
│   ├── tokenizer.json
│   └── ...
```

## 2. Silero VAD 다운로드

### 2.1 방법 1: Python 스크립트

```bash
python download_vad.py
```

`download_vad.py`:
```python
import torch

print("Downloading Silero VAD model...")
model, utils = torch.hub.load(
    repo_or_dir="snakers4/silero-vad",
    model="silero_vad",
    force_reload=False,
    onnx=False,
    source="local"  # 로컬에서 로드하도록 설정
)
print("Silero VAD model downloaded successfully!")
```

### 2.2 방법 2: Torch Hub 캐시 활용

최초 1회 네트워크 연결 시 다운로드되며, 이후에는 캐시에서 로드됩니다.

```bash
# 캐시 위치 확인 (Windows)
# %USERPROFILE%/.cache/torch/hub/snakers4_silero-vad_master/
```

## 3. 로컬 모델 사용 방법

### 3.1 CLI에서 모델 경로 지정

```bash
python main.py --input meeting.mp3 --model models/whisper-large-v3
```

### 3.2 GUI에서 모델 선택

GUI의 "모델" 드롭다운에서 로컬 경로를 선택하거나 설정 파일을 수정합니다.

## 4. 완전 오프라인 배포

### 4.1 모델 포함 배포

```bash
# 프로젝트 루트에 models 폴더 생성
mkdir -p models

# 모든 모델 다운로드
huggingface-cli download Systran/faster-whisper-large-v3 --local-dir models/whisper-large-v3
```

### 4.2 배포용 디렉토리 구조

```
DictationApp/
├── DictationApp.exe
├── app/
│   ├── core/
│   └── ui/
├── models/
│   └── whisper-large-v3/
│       └── (모델 파일들)
├── FFmpeg/
│   └── bin/
│       └── ffmpeg.exe
└── README.md
```

### 4.3 config.py 수정

모델 경로를 기본값으로 설정:

```python
def get_model_path(self) -> Optional[str]:
    if Path(self.model_name).exists():
        return str(self.model_name)

    model_map = {
        "large-v3": "models/whisper-large-v3",
        ...
    }
    return model_map.get(self.model_name, self.model_name)
```

## 5. 모델 크기 비교

| 모델 | 크기 | 정확도 | 속도 (RTX 4090) |
|------|------|--------|-----------------|
| large-v3 | ~3.0GB | 최고 | ~0.3x 실시간 |
| large-v2 | ~3.0GB | 높음 | ~0.3x 실시간 |
| medium | ~1.5GB | 중간 | ~0.5x 실시간 |
| small | ~460MB | 보통 | ~0.8x 실시간 |
| base | ~140MB | 낮음 | ~1.2x 실시간 |

## 6. 디스크 요구사항

### 최소 (base 모델)
- 모델: ~140MB
- 임시 파일: 최대 ~500MB (90분 오디오)
- 총계: ~700MB

### 권장 (large-v3)
- 모델: ~3.0GB
- 임시 파일: 최대 ~500MB (90분 오디오)
- 출력 파일: ~50MB
- 총계: ~3.5GB

## 7. 메모리 요구사항

### GPU VRAM
- large-v3: ~10GB (int8_float16)
- medium: ~4GB (int8_float16)
- small: ~2GB (int8_float16)
- base: ~1GB (int8_float16)

### CPU RAM
- 최소: 8GB
- 권장: 16GB 이상

## 8. 오프라인 검증

### 네트워크 차단 상태에서 테스트

```bash
# 네트워크 끊기 (Windows)
ipconfig /release

# 테스트 실행
python main.py --input meeting.mp3 --output test --model models/whisper-large-v3

# 네트워스 복구
ipconfig /renew
```

### 예상 결과

- ✅ FFmpeg 변환: 성공
- ✅ VAD 분할: 성공 (캐시에서 로드)
- ✅ STT 인식: 성공 (로컬 모델)
- ✅ 후처리: 성공
- ✅ 파일 내보내기: 성공

## 9. 문제 해결

### 9.1 모델 로드 실패

**오류**: `OSError: Can't load model from models/whisper-large-v3`

**해결**:
1. 모델 파일 존재 확인
2. 파일 권한 확인
3. 모델 파일完整性 검증 (SHA256)

### 9.2 Silero VAD 로드 실패

**오류**: `RuntimeError: Failed to load VAD model`

**해결**:
1. torch.hub 캐시 확인
2. 네트워크 연결 후 1회 실행
3. 또는 로컬 모델 파일 사용

### 9.3 GPU 메모리 부족

**오류**: `CUDA out of memory`

**해결**:
1. `--compute-type int8` 사용
2. 작은 모델 사용 (medium/small)
3. 다른 GPU 프로세스 종료

## 10. 추가 리소스

### 모델 소스
- [faster-whisper GitHub](https://github.com/SYSTRAN/faster-whisper)
- [Silero VAD GitHub](https://github.com/snakers4/silero-vad)

### 공식 문서
- [faster-whisper docs](https://github.com/SYSTRAN/faster-whisper/blob/master/README.md)
- [HuggingFace Model Hub](https://huggingface.co/models)
