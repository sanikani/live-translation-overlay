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
from src.translation.translator import TranslationService


DEFAULT_MICROPHONE_LABEL = "기본 마이크"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("실시간 다국어 번역 자막 - Phase 2")
        self.resize(820, 720)

        self._last_final_text = ""

        self._speech_service = SpeechRecognitionService(self)
        self._speech_service.partial_text.connect(self._show_partial_text)
        self._speech_service.final_text.connect(self._handle_final_text)
        self._speech_service.status_changed.connect(self._set_speech_status)
        self._speech_service.error_occurred.connect(self._show_speech_error)

        self._translation_service = TranslationService(self)
        self._translation_service.translation_ready.connect(
            self._append_translation
        )
        self._translation_service.status_changed.connect(
            self._set_translation_status
        )
        self._translation_service.error_occurred.connect(
            self._show_translation_error
        )

        self._build_ui()
        self._refresh_microphones()
        self._refresh_translation_status()

    def _build_ui(self) -> None:
        root = QWidget(self)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("실시간 한국어 → 영어 번역")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        layout.addWidget(title)

        description = QLabel(
            "마이크를 선택하고 시작 버튼을 누르면 한국어 발표를 인식합니다. "
            "확정된 문장만 영어로 번역하므로 말하는 중간 결과는 번역하지 않습니다."
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
        self.start_button = QPushButton("음성 인식 및 번역 시작")
        self.stop_button = QPushButton("중지")
        self.stop_button.setEnabled(False)

        self.start_button.clicked.connect(self._start_recognition)
        self.stop_button.clicked.connect(self._stop_recognition)

        button_row.addWidget(self.start_button)
        button_row.addWidget(self.stop_button)
        layout.addLayout(button_row)

        status_row = QHBoxLayout()
        status_row.addWidget(QLabel("음성 인식"))
        self.speech_status_label = QLabel("대기 중")
        self.speech_status_label.setStyleSheet("font-weight: 700;")
        status_row.addWidget(self.speech_status_label)

        status_row.addSpacing(24)
        status_row.addWidget(QLabel("영어 번역"))
        self.translation_status_label = QLabel("확인 중")
        self.translation_status_label.setStyleSheet("font-weight: 700;")
        status_row.addWidget(self.translation_status_label)
        status_row.addStretch(1)
        layout.addLayout(status_row)

        partial_title = QLabel("현재 듣는 내용")
        partial_title.setStyleSheet("font-weight: 700;")
        layout.addWidget(partial_title)

        self.partial_label = QLabel(
            "말을 시작하면 여기에 임시 인식 결과가 표시됩니다."
        )
        self.partial_label.setWordWrap(True)
        self.partial_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.partial_label.setMinimumHeight(72)
        self.partial_label.setStyleSheet(
            "padding: 12px; border: 1px solid #cccccc; border-radius: 6px; "
            "font-size: 17px;"
        )
        layout.addWidget(self.partial_label)

        korean_title = QLabel("확정된 한국어")
        korean_title.setStyleSheet("font-weight: 700;")
        layout.addWidget(korean_title)

        self.transcript_box = QPlainTextEdit()
        self.transcript_box.setReadOnly(True)
        self.transcript_box.setPlaceholderText(
            "확정된 한국어 문장이 이곳에 쌓입니다."
        )
        self.transcript_box.setStyleSheet("font-size: 16px;")
        layout.addWidget(self.transcript_box, 1)

        english_title = QLabel("영어 번역")
        english_title.setStyleSheet("font-weight: 700;")
        layout.addWidget(english_title)

        self.translation_box = QPlainTextEdit()
        self.translation_box.setReadOnly(True)
        self.translation_box.setPlaceholderText(
            "확정된 한국어 문장의 영어 번역이 이곳에 표시됩니다."
        )
        self.translation_box.setStyleSheet("font-size: 17px;")
        layout.addWidget(self.translation_box, 1)

        self.translation_error_label = QLabel("")
        self.translation_error_label.setWordWrap(True)
        self.translation_error_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(self.translation_error_label)

        clear_button = QPushButton("내용 지우기")
        clear_button.clicked.connect(self._clear_text)
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
                "마이크 목록을 불러오지 못했습니다. "
                f"기본 마이크는 계속 사용할 수 있습니다.\n\n{exc}",
            )
        finally:
            self.microphone_combo.blockSignals(False)

    def _refresh_translation_status(self) -> None:
        settings = Settings.from_env()
        if settings.translator_configured:
            self._set_translation_status("번역 준비됨")
        else:
            self._set_translation_status("설정 필요")

    def _start_recognition(self) -> None:
        settings = Settings.from_env()
        if not settings.speech_configured:
            QMessageBox.information(
                self,
                "Azure Speech 설정 필요",
                "프로젝트 루트의 .env 파일에 Azure Speech Key와 Region을 "
                "입력해야 합니다.\n설정 방법은 docs/SETUP.md를 참고해 주세요.",
            )
            return

        if not settings.translator_configured:
            self._set_translation_status("설정 필요")
            self.translation_error_label.setText(
                "Translator 설정이 없어 현재는 한국어 음성 인식만 동작합니다. "
                "docs/SETUP.md를 참고해 Translator Key를 추가하면 영어 번역도 "
                "자동으로 시작됩니다."
            )
        else:
            self.translation_error_label.setText("")
            self._set_translation_status("번역 준비됨")

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
            text
            if text
            else "말을 시작하면 여기에 임시 인식 결과가 표시됩니다."
        )

    def _handle_final_text(self, text: str) -> None:
        normalized = text.strip()
        if not normalized:
            return

        # SDK 이벤트가 바로 연속해서 같은 확정 문장을 전달한 경우 중복 요청을 막는다.
        if normalized == self._last_final_text:
            return

        self._last_final_text = normalized
        self.transcript_box.appendPlainText(normalized)

        settings = Settings.from_env()
        if settings.translator_configured:
            self._translation_service.translate_async(
                normalized,
                target_language="en",
            )

    def _append_translation(
        self,
        source_text: str,
        target_language: str,
        translated_text: str,
    ) -> None:
        if target_language != "en":
            return

        self.translation_box.appendPlainText(translated_text)
        self.translation_error_label.setText("")

    def _set_speech_status(self, status: str) -> None:
        self.speech_status_label.setText(status)

        if (
            status in {"중단됨", "대기 중"}
            and not self._speech_service.is_running
        ):
            self._set_controls_idle()

    def _set_translation_status(self, status: str) -> None:
        self.translation_status_label.setText(status)

    def _show_speech_error(self, message: str) -> None:
        QMessageBox.critical(self, "음성 인식 오류", message)
        self._set_controls_idle()

    def _show_translation_error(self, message: str) -> None:
        # 번역 오류 때문에 발표용 음성 인식까지 중단하지 않는다.
        self.translation_error_label.setText(message)

    def _clear_text(self) -> None:
        self.transcript_box.clear()
        self.translation_box.clear()
        self.partial_label.setText(
            "말을 시작하면 여기에 임시 인식 결과가 표시됩니다."
        )
        self.translation_error_label.setText("")
        self._last_final_text = ""

    def _set_controls_idle(self) -> None:
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.microphone_combo.setEnabled(True)
        self.refresh_button.setEnabled(True)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API 이름 유지
        if self._speech_service.is_running:
            self._speech_service.stop()

        self._translation_service.shutdown()
        event.accept()
