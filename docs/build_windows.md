# Windows 빌드 가이드

## 필수 요소

1. **Python 3.10+**
2. **FFmpeg** (PATH에 포함)
3. **PyInstaller**

## 개발 환경 설정

```bash
# 가상 환경 생성
python -m venv venv
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

## CLI 실행 테스트

```bash
python main.py --input sample.mp3 --output test_output
```

## GUI 실행 테스트

```bash
python app/ui/gui.py
```

## PyInstaller로 exe 빌드

### 1. PyInstaller 설치

```bash
pip install pyinstaller
```

### 2. 빌드 스크립트 작성

`build.spec` 파일 생성:

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app/ui/gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app', 'app'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'torch',
        'faster_whisper',
        'numpy',
        'scipy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DictationApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)
```

### 3. 빌드 실행

```bash
pyinstaller build.spec
```

또는 간단히:

```bash
pyinstaller --onefile --windowed --name DictationApp --icon assets/icon.ico app/ui/gui.py
```

### 4. 결과물

`dist/DictationApp.exe` 파일이 생성됩니다.

## 배포 패키지 구조

```
DictationApp/
├── DictationApp.exe
├── FFmpeg/
│   └── bin/
│       ├── ffmpeg.exe
│       └── ffprobe.exe
├── models/
│   └── whisper-large-v3/
│       └── (모델 파일들)
└── README.md
```

## 오프라인 설치 가이드

### 사용자 매뉴얼

1. **FFmpeg 설치**: `FFmpeg` 폴더 내용을 시스템 PATH에 추가하거나 환경 변수 설정
2. **모델 파일**: `models` 폴더에 사전 다운로드한 모델 파일 배치
3. **실행**: `DictationApp.exe` 더블 클릭

### 오프라인 모델 다운로드

```bash
# Whisper 모델
huggingface-cli download Systran/faster-whisper-large-v3 --local-dir models/whisper-large-v3

# Silero VAD
python -c "import torch; torch.hub.load('snakers4/silero-vad', model='silero_vad')"
```

## 트러블슈팅

### 빌드 실패

1. `--debug` 옵션 추가로 로그 확인
2. `hiddenimports`에 누락된 모듈 추가
3. PyInstaller 버전 확인 및 업데이트

### 실행 시 모듈 못 찾음

1. `--hiddenimports` 추가
2. `datas`에 필요한 파일 추가
3. `.spec` 파일 수정 후 재빌드

### FFmpeg 오류

1. FFmpeg가 실행 파일과 같은 폴더에 있는지 확인
2. PATH 환경 변수 확인

## 대안: Briefcase 사용

PyInstaller 대신 Briefcase로도 빌드 가능:

```bash
pip install briefcase
briefcase create windows
briefcase build windows
briefcase package windows
```

## 추가 최적화

1. **UPX**: 실행 파일 크기 압축
   ```bash
   --upx-dir C:/upx
   ```

2. **모듈 제외**: 불필요한 모듈 exclude
   ```python
   excludes=['tkinter', 'matplotlib', ...]
   ```

3. **싱 파일 vs 폴더**: 디버깅 쉽게 하려면 `--onefile` 대신 `--onedir`
