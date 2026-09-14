from __future__ import annotations

import sounddevice as sd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.config.settings import Settings
from src.speech.speech_recognizer import SpeechRecognitionService


DEFAULT_MICROPHONE_LABEL = "기본 마이크"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("실시간 다국어 번역 자막 - Phase 1")
        self.resize(760, 560)

        self._speech_service = SpeechRecognitionService(self)
        self._speech_service.partial_text.connect(self._show_partial_text)
        self._speech_service.final_text.connect(self._append_final_text)
        self._speech_service.status_changed.connect(self._set_status)
        self._speech_service.error_occurred.connect(self._show_error)

        self._build_ui()
        self._refresh_microphones()

    def _build_ui(self) -> None:
        root = QWidget(self)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel("실시간 한국어 음성 인식")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        layout.addWidget(title)

        description = QLabel(
            "마이크를 선택하고 '음성 인식 시작'을 누른 뒤 평소처럼 말해 보세요. "
            "현재 단계에서는 한국어 음성을 글자로 바꾸는 기능만 검증합니다."
        )
        description.setWordWrap(True)
        description.setStyleSheet("font-size: 14px;")
        layout.addWidget(description)

        microphone_row = QHBoxLayout()
        microphone_label = QLabel("마이크")
        self.microphone_combo = QComboBox()
        self.refresh_button = QPushButton("새로고침")
        self.refresh_button.clicked.connect(self._refresh_microphones)

        microphone_row.addWidget(microphone_label)
        microphone_row.addWidget(self.microphone_combo, 1)
        microphone_row.addWidget(self.refresh_button)
        layout.addLayout(microphone_row)

        button_row = QHBoxLayout()
        self.start_button = QPushButton("음성 인식 시작")
        self.stop_button = QPushButton("중지")
        self.stop_button.setEnabled(False)

        self.start_button.clicked.connect(self._start_recognition)
        self.stop_button.clicked.connect(self._stop_recognition)

        button_row.addWidget(self.start_button)
        button_row.addWidget(self.stop_button)
        layout.addLayout(button_row)

        status_row = QHBoxLayout()
        status_title = QLabel("상태")
        self.status_label = QLabel("대기 중")
        self.status_label.setStyleSheet("font-weight: 700;")
        status_row.addWidget(status_title)
        status_row.addWidget(self.status_label)
        status_row.addStretch(1)
        layout.addLayout(status_row)

        partial_title = QLabel("현재 듣는 내용")
        partial_title.setStyleSheet("font-weight: 700;")
        layout.addWidget(partial_title)

        self.partial_label = QLabel("말을 시작하면 여기에 임시 인식 결과가 표시됩니다.")
        self.partial_label.setWordWrap(True)
        self.partial_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.partial_label.setMinimumHeight(80)
        self.partial_label.setStyleSheet(
            "padding: 12px; border: 1px solid #cccccc; border-radius: 6px; "
            "font-size: 17px;"
        )
        layout.addWidget(self.partial_label)

        final_title = QLabel("확정된 문장")
        final_title.setStyleSheet("font-weight: 700;")
        layout.addWidget(final_title)

        self.transcript_box = QPlainTextEdit()
        self.transcript_box.setReadOnly(True)
        self.transcript_box.setPlaceholderText("확정된 한국어 문장이 이곳에 쌓입니다.")
        self.transcript_box.setStyleSheet("font-size: 17px;")
        layout.addWidget(self.transcript_box, 1)

        clear_button = QPushButton("내용 지우기")
        clear_button.clicked.connect(self.transcript_box.clear)
        layout.addWidget(clear_button)

        self.setCentralWidget(root)

    def _refresh_microphones(self) -> None:
        current = self.microphone_combo.currentText()

        self.microphone_combo.blockSignals(True)
        self.microphone_combo.clear()
        self.microphone_combo.addItem(DEFAULT_MICROPHONE_LABEL, None)

        try:
            names: list[str] = []
            for device in sd.query_devices():
                if int(device.get("max_input_channels", 0)) <= 0:
                    continue

                name = str(device.get("name", "")).strip()
                if name and name not in names:
                    names.append(name)

            for name in names:
                self.microphone_combo.addItem(name, name)

            index = self.microphone_combo.findText(current)
            if index >= 0:
                self.microphone_combo.setCurrentIndex(index)
        except Exception as exc:
            QMessageBox.warning(
                self,
                "마이크 확인 실패",
                f"마이크 목록을 불러오지 못했습니다. 기본 마이크는 계속 사용할 수 있습니다.\n\n{exc}",
            )
        finally:
            self.microphone_combo.blockSignals(False)

    def _start_recognition(self) -> None:
        settings = Settings.from_env()
        if not settings.is_configured:
            QMessageBox.information(
                self,
                "Azure Speech 설정 필요",
                "프로젝트 루트의 .env 파일에 Azure Speech Key와 Region을 입력해야 합니다.\n"
                "설정 방법은 docs/SETUP.md를 참고해 주세요.",
            )
            return

        microphone_name = self.microphone_combo.currentData()

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.microphone_combo.setEnabled(False)
        self.refresh_button.setEnabled(False)

        self._speech_service.start(microphone_name)

        if not self._speech_service.is_running:
            self._set_controls_idle()

    def _stop_recognition(self) -> None:
        self._speech_service.stop()
        self._set_controls_idle()

    def _show_partial_text(self, text: str) -> None:
        self.partial_label.setText(
            text if text else "말을 시작하면 여기에 임시 인식 결과가 표시됩니다."
        )

    def _append_final_text(self, text: str) -> None:
        self.transcript_box.appendPlainText(text)

    def _set_status(self, status: str) -> None:
        self.status_label.setText(status)

        if status in {"중단됨", "대기 중"} and not self._speech_service.is_running:
            self._set_controls_idle()

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, "음성 인식 오류", message)
        self._set_controls_idle()

    def _set_controls_idle(self) -> None:
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.microphone_combo.setEnabled(True)
        self.refresh_button.setEnabled(True)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API 이름 유지
        if self._speech_service.is_running:
            self._speech_service.stop()
        event.accept()
