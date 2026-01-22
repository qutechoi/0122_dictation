import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QSpinBox, QTextEdit,
    QFileDialog, QProgressBar, QGroupBox, QCheckBox,
)
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QFont

from app.core.config import Config
from main import DictationPipeline

logger = logging.getLogger(__name__)


class PipelineThread(QThread):
    progress = Signal(str)
    finished = Signal(bool, str)
    log = Signal(str)

    def __init__(self, config: Config):
        super().__init__()
        self.config = config

    def run(self):
        try:
            pipeline = DictationPipeline(self.config)

            original_callback = pipeline.progress_callback

            def callback_wrapper(current, total, message):
                self.progress.emit(f"{message} ({current}/{total})")
                self.log.emit(f"[INFO] {message}")

            pipeline.progress_callback = callback_wrapper

            success = pipeline.run()

            if success:
                self.finished.emit(True, "처리 완료!")
            else:
                self.finished.emit(False, "처리 실패")

        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            self.log.emit(f"[ERROR] {str(e)}")
            self.finished.emit(False, f"오류: {str(e)}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pipeline_thread = None
        self.init_ui()
        self.setup_logging()

    def init_ui(self):
        self.setWindowTitle("MP3 Dictation & Meeting Minutes Generator")
        self.setMinimumSize(900, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        main_layout.addWidget(self.create_file_group())
        main_layout.addWidget(self.create_model_group())
        main_layout.addWidget(self.create_meeting_info_group())
        main_layout.addWidget(self.create_vad_group())
        main_layout.addWidget(self.create_progress_group())
        main_layout.addWidget(self.create_log_group())
        main_layout.addWidget(self.create_button_group())

    def create_file_group(self) -> QGroupBox:
        group = QGroupBox("파일 설정")
        layout = QVBoxLayout()

        row1 = QHBoxLayout()
        self.input_label = QLabel("입력 파일: 미선택")
        row1.addWidget(self.input_label)
        select_btn = QPushButton("파일 선택")
        select_btn.clicked.connect(self.select_input_file)
        row1.addWidget(select_btn)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("출력 폴더:"))
        self.output_edit = QLineEdit("output")
        row2.addWidget(self.output_edit)
        output_btn = QPushButton("폴더 선택")
        output_btn.clicked.connect(self.select_output_folder)
        row2.addWidget(output_btn)
        layout.addLayout(row2)

        group.setLayout(layout)
        return group

    def create_model_group(self) -> QGroupBox:
        group = QGroupBox("모델 설정")
        layout = QHBoxLayout()

        layout.addWidget(QLabel("모델:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["large-v3", "large-v2", "medium", "small", "base"])
        self.model_combo.setCurrentText("large-v3")
        layout.addWidget(self.model_combo)

        layout.addWidget(QLabel("Compute Type:"))
        self.compute_combo = QComboBox()
        self.compute_combo.addItems(["int8_float16", "float16", "float32", "int8"])
        self.compute_combo.setCurrentText("int8_float16")
        layout.addWidget(self.compute_combo)

        layout.addWidget(QLabel("Language:"))
        self.language_combo = QComboBox()
        self.language_combo.addItems(["ko", "en", "auto", "ja", "zh"])
        self.language_combo.setCurrentText("ko")
        layout.addWidget(self.language_combo)

        group.setLayout(layout)
        return group

    def create_meeting_info_group(self) -> QGroupBox:
        group = QGroupBox("회의 정보 (선택)")
        layout = QVBoxLayout()

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("회의명:"))
        self.title_edit = QLineEdit()
        row1.addWidget(self.title_edit)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("일시:"))
        self.date_edit = QLineEdit()
        row2.addWidget(self.date_edit)
        row2.addWidget(QLabel("참석자:"))
        self.attendees_edit = QLineEdit()
        row2.addWidget(self.attendees_edit)
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("프로젝트:"))
        self.project_edit = QLineEdit()
        row3.addWidget(self.project_edit)
        layout.addLayout(row3)

        row4 = QHBoxLayout()
        row4.addWidget(QLabel("Initial Prompt (용어 사전):"))
        self.prompt_edit = QLineEdit()
        self.prompt_edit.setPlaceholderText("예: LIS, EMR, QC, HbA1c...")
        row4.addWidget(self.prompt_edit)
        layout.addLayout(row4)

        group.setLayout(layout)
        return group

    def create_vad_group(self) -> QGroupBox:
        group = QGroupBox("VAD 설정")
        layout = QHBoxLayout()

        layout.addWidget(QLabel("Max Segment (ms):"))
        self.max_segment_spin = QSpinBox()
        self.max_segment_spin.setRange(10000, 60000)
        self.max_segment_spin.setValue(30000)
        self.max_segment_spin.setSuffix(" ms")
        layout.addWidget(self.max_segment_spin)

        layout.addWidget(QLabel("Min Silence (ms):"))
        self.min_silence_spin = QSpinBox()
        self.min_silence_spin.setRange(500, 5000)
        self.min_silence_spin.setValue(2000)
        self.min_silence_spin.setSuffix(" ms")
        layout.addWidget(self.min_silence_spin)

        group.setLayout(layout)
        return group

    def create_progress_group(self) -> QGroupBox:
        group = QGroupBox("진행 상황")
        layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("대기 중...")
        self.status_label.setFont(QFont("", 10, QFont.Bold))
        layout.addWidget(self.status_label)

        group.setLayout(layout)
        return group

    def create_log_group(self) -> QGroupBox:
        group = QGroupBox("로그")
        layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text)

        group.setLayout(layout)
        return group

    def create_button_group(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout()

        self.start_btn = QPushButton("시작")
        self.start_btn.clicked.connect(self.start_pipeline)
        self.start_btn.setMinimumHeight(40)
        self.start_btn.setFont(QFont("", 10, QFont.Bold))
        layout.addWidget(self.start_btn)

        self.open_folder_btn = QPushButton("결과 폴더 열기")
        self.open_folder_btn.clicked.connect(self.open_output_folder)
        self.open_folder_btn.setMinimumHeight(40)
        self.open_folder_btn.setEnabled(False)
        layout.addWidget(self.open_folder_btn)

        widget.setLayout(layout)
        return widget

    def select_input_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "MP3 파일 선택",
            "",
            "Audio Files (*.mp3 *.MP3)"
        )
        if file_path:
            self.input_file_path = file_path
            self.input_label.setText(f"입력 파일: {Path(file_path).name}")

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "출력 폴더 선택"
        )
        if folder:
            self.output_edit.setText(folder)

    def start_pipeline(self):
        if not hasattr(self, 'input_file_path'):
            self.append_log("[ERROR] 입력 파일을 선택해주세요.")
            return

        config = Config(
            input_file=self.input_file_path,
            output_dir=self.output_edit.text(),
            model_name=self.model_combo.currentText(),
            compute_type=self.compute_combo.currentText(),
            language=self.language_combo.currentText(),
            num_workers=1,
            initial_prompt=self.prompt_edit.text() or None,
            meeting_title=self.title_edit.text() or None,
            meeting_date=self.date_edit.text() or None,
            attendees=self.attendees_edit.text() or None,
            project_name=self.project_edit.text() or None,
            max_segment_duration_ms=self.max_segment_spin.value(),
            min_silence_duration_ms=self.min_silence_spin.value(),
        )

        self.start_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.open_folder_btn.setEnabled(False)
        self.status_label.setText("처리 중...")
        self.append_log("[INFO] 파이프라인 시작...")

        self.pipeline_thread = PipelineThread(config)
        self.pipeline_thread.progress.connect(self.update_progress)
        self.pipeline_thread.finished.connect(self.on_finished)
        self.pipeline_thread.log.connect(self.append_log)
        self.pipeline_thread.start()

    def update_progress(self, message: str):
        self.status_label.setText(message)
        self.progress_bar.setValue(self.progress_bar.value() + 5)

    def on_finished(self, success: bool, message: str):
        self.start_btn.setEnabled(True)
        self.open_folder_btn.setEnabled(True)
        self.progress_bar.setValue(100 if success else 0)

        if success:
            self.status_label.setText("완료!")
            self.append_log(f"[SUCCESS] {message}")
        else:
            self.status_label.setText("실패")
            self.append_log(f"[ERROR] {message}")

    def open_output_folder(self):
        import subprocess
        import platform

        folder = self.output_edit.text()
        folder_path = Path(folder)

        if folder_path.exists():
            if platform.system() == "Windows":
                subprocess.run(['explorer', str(folder_path)])
            elif platform.system() == "Darwin":
                subprocess.run(['open', str(folder_path)])
            else:
                subprocess.run(['xdg-open', str(folder_path)])

    def append_log(self, message: str):
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def setup_logging(self):
        logging.getLogger().addHandler(
            QtLogHandler(self.append_log)
        )


class QtLogHandler(logging.Handler):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def emit(self, record):
        msg = self.format(record)
        self.callback(f"[{record.levelname}] {msg}")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
