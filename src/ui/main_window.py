from __future__ import annotations

import sounddevice as sd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from src.config.settings import Settings
from src.speech.speech_recognizer import SpeechRecognitionService
from src.translation.translator import TranslationService
from src.ui.overlay_window import SubtitleOverlayWindow


DEFAULT_MICROPHONE_LABEL = "기본 마이크"

LANGUAGE_OPTIONS: tuple[tuple[str, str], ...] = (
    ("en", "English"),
    ("zh-Hans", "中文"),
    ("vi", "Tiếng Việt"),
    ("th", "ภาษาไทย"),
)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("실시간 다국어 번역 자막")
        self.resize(860, 780)

        self._last_final_text = ""
        self._language_checkboxes: dict[str, QCheckBox] = {}

        self._overlay = SubtitleOverlayWindow()

        self._speech_service = SpeechRecognitionService(self)
        self._speech_service.partial_text.connect(self._show_partial_text)
        self._speech_service.final_text.connect(self._handle_final_text)
        self._speech_service.status_changed.connect(self._set_speech_status)
        self._speech_service.error_occurred.connect(self._show_speech_error)

        self._translation_service = TranslationService(self)
        self._translation_service.translation_ready.connect(
            self._append_translation_batch
        )
        self._translation_service.status_changed.connect(
            self._set_translation_status
        )
        self._translation_service.error_occurred.connect(
            self._show_translation_error
        )

        self._build_ui()
        self._refresh_microphones()
        self._refresh_screens()
        self._refresh_translation_status()

    def _build_ui(self) -> None:
        root = QWidget(self)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("실시간 다국어 번역 자막")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        layout.addWidget(title)

        description = QLabel(
            "마이크와 번역 언어를 선택한 뒤 시작하세요. "
            "확정된 한국어 문장을 여러 언어로 동시에 번역해 "
            "선택한 화면의 강의자료 위에 자막으로 표시합니다."
        )
        description.setWordWrap(True)
        description.setStyleSheet("font-size: 14px;")
        layout.addWidget(description)

        microphone_row = QHBoxLayout()
        microphone_row.addWidget(QLabel("마이크"))

        self.microphone_combo = QComboBox()
        microphone_row.addWidget(self.microphone_combo, 1)

        self.refresh_button = QPushButton("새로고침")
        self.refresh_button.clicked.connect(self._refresh_microphones)
        microphone_row.addWidget(self.refresh_button)
        layout.addLayout(microphone_row)

        language_group = QGroupBox("번역 언어")
        language_layout = QGridLayout(language_group)

        for index, (code, display_name) in enumerate(LANGUAGE_OPTIONS):
            checkbox = QCheckBox(display_name)
            checkbox.setChecked(code in {"en", "zh-Hans", "vi"})
            self._language_checkboxes[code] = checkbox
            language_layout.addWidget(checkbox, index // 2, index % 2)

        layout.addWidget(language_group)

        overlay_group = QGroupBox("자막 화면 설정")
        overlay_layout = QGridLayout(overlay_group)

        overlay_layout.addWidget(QLabel("표시할 화면"), 0, 0)
        self.screen_combo = QComboBox()
        self.screen_combo.currentIndexChanged.connect(
            self._apply_overlay_screen
        )
        overlay_layout.addWidget(self.screen_combo, 0, 1, 1, 2)

        overlay_layout.addWidget(QLabel("자막 위치"), 1, 0)
        self.position_combo = QComboBox()
        self.position_combo.addItem("화면 하단", "bottom")
        self.position_combo.addItem("화면 상단", "top")
        self.position_combo.currentIndexChanged.connect(
            self._apply_overlay_position
        )
        overlay_layout.addWidget(self.position_combo, 1, 1, 1, 2)

        overlay_layout.addWidget(QLabel("글자 크기"), 2, 0)
        self.font_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_slider.setRange(18, 52)
        self.font_slider.setValue(28)
        self.font_slider.valueChanged.connect(self._apply_overlay_font_size)
        overlay_layout.addWidget(self.font_slider, 2, 1)

        self.font_size_label = QLabel("28")
        self.font_size_label.setMinimumWidth(32)
        overlay_layout.addWidget(self.font_size_label, 2, 2)

        layout.addWidget(overlay_group)

        button_row = QHBoxLayout()

        self.start_button = QPushButton("실시간 번역 시작")
        self.start_button.clicked.connect(self._start_recognition)
        button_row.addWidget(self.start_button)

        self.stop_button = QPushButton("중지")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self._stop_recognition)
        button_row.addWidget(self.stop_button)

        layout.addLayout(button_row)

        status_row = QHBoxLayout()
        status_row.addWidget(QLabel("음성 인식"))

        self.speech_status_label = QLabel("대기 중")
        self.speech_status_label.setStyleSheet("font-weight: 700;")
        status_row.addWidget(self.speech_status_label)

        status_row.addSpacing(24)
        status_row.addWidget(QLabel("번역"))

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
        self.partial_label.setMinimumHeight(64)
        self.partial_label.setStyleSheet(
            "padding: 12px; border: 1px solid #cccccc; "
            "border-radius: 6px; font-size: 16px;"
        )
        layout.addWidget(self.partial_label)

        history_title = QLabel("확정 문장 / 번역 기록")
        history_title.setStyleSheet("font-weight: 700;")
        layout.addWidget(history_title)

        self.history_box = QPlainTextEdit()
        self.history_box.setReadOnly(True)
        self.history_box.setPlaceholderText(
            "확정된 한국어와 선택한 언어의 번역 결과가 여기에 쌓입니다."
        )
        self.history_box.setStyleSheet("font-size: 15px;")
        layout.addWidget(self.history_box, 1)

        self.translation_error_label = QLabel("")
        self.translation_error_label.setWordWrap(True)
        self.translation_error_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(self.translation_error_label)

        clear_button = QPushButton("자막 / 기록 지우기")
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

    def _refresh_screens(self) -> None:
        current_index = self.screen_combo.currentData()

        self.screen_combo.blockSignals(True)
        self.screen_combo.clear()

        screens = QApplication.screens()
        for index, screen in enumerate(screens):
            geometry = screen.geometry()
            label = (
                f"화면 {index + 1} - {screen.name()} "
                f"({geometry.width()}x{geometry.height()})"
            )
            self.screen_combo.addItem(label, index)

        if current_index is not None:
            combo_index = self.screen_combo.findData(current_index)
            if combo_index >= 0:
                self.screen_combo.setCurrentIndex(combo_index)

        self.screen_combo.blockSignals(False)
        self._apply_overlay_screen()

    def _selected_language_codes(self) -> list[str]:
        return [
            code
            for code, _display_name in LANGUAGE_OPTIONS
            if self._language_checkboxes[code].isChecked()
        ]

    def _selected_language_names(self) -> dict[str, str]:
        selected = set(self._selected_language_codes())
        return {
            code: display_name
            for code, display_name in LANGUAGE_OPTIONS
            if code in selected
        }

    def _selected_screen(self):
        screens = QApplication.screens()
        screen_index = self.screen_combo.currentData()

        if (
            isinstance(screen_index, int)
            and 0 <= screen_index < len(screens)
        ):
            return screens[screen_index]

        return QApplication.primaryScreen()

    def _configure_overlay(self) -> None:
        self._overlay.configure(
            language_names=self._selected_language_names(),
            screen=self._selected_screen(),
            position=self.position_combo.currentData() or "bottom",
            font_size=self.font_slider.value(),
        )

    def _apply_overlay_screen(self) -> None:
        self._overlay.set_target_screen(self._selected_screen())

    def _apply_overlay_position(self) -> None:
        self._overlay.set_position(
            self.position_combo.currentData() or "bottom"
        )

    def _apply_overlay_font_size(self, value: int) -> None:
        self.font_size_label.setText(str(value))
        self._overlay.set_font_size(value)

    def _refresh_translation_status(self) -> None:
        settings = Settings.from_env()
        if settings.translator_configured:
            self._set_translation_status("번역 준비됨")
        else:
            self._set_translation_status("설정 필요")

    def _start_recognition(self) -> None:
        selected_languages = self._selected_language_codes()
        if not selected_languages:
            QMessageBox.information(
                self,
                "번역 언어 선택",
                "번역할 언어를 한 개 이상 선택해 주세요.",
            )
            return

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
                "docs/SETUP.md를 참고해 Translator Key를 추가해 주세요."
            )
        else:
            self.translation_error_label.setText("")
            self._set_translation_status("번역 준비됨")

        self._configure_overlay()
        self._overlay.clear_subtitles()

        microphone_name = self.microphone_combo.currentData()

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.microphone_combo.setEnabled(False)
        self.refresh_button.setEnabled(False)
        self.screen_combo.setEnabled(False)

        for checkbox in self._language_checkboxes.values():
            checkbox.setEnabled(False)

        self._speech_service.start(microphone_name)

        if not self._speech_service.is_running:
            self._set_controls_idle()

    def _stop_recognition(self) -> None:
        self._speech_service.stop()
        self._overlay.hide()
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

        if normalized == self._last_final_text:
            return

        self._last_final_text = normalized
        self.history_box.appendPlainText(f"[한국어] {normalized}")

        settings = Settings.from_env()
        selected_languages = self._selected_language_codes()

        if settings.translator_configured and selected_languages:
            self._translation_service.translate_many_async(
                normalized,
                selected_languages,
            )

    def _append_translation_batch(
        self,
        source_text: str,
        translations: object,
    ) -> None:
        if not isinstance(translations, dict):
            return

        names = dict(LANGUAGE_OPTIONS)
        selected_codes = self._selected_language_codes()

        ordered_translations: dict[str, str] = {}
        for code in selected_codes:
            translated_text = str(translations.get(code, "")).strip()
            if not translated_text:
                continue

            ordered_translations[code] = translated_text
            display_name = names.get(code, code)
            self.history_box.appendPlainText(
                f"[{display_name}] {translated_text}"
            )

        self.history_box.appendPlainText("")

        if ordered_translations:
            self._overlay.update_subtitles(ordered_translations)

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
        self._overlay.hide()
        self._set_controls_idle()

    def _show_translation_error(self, message: str) -> None:
        self.translation_error_label.setText(message)

    def _clear_text(self) -> None:
        self.history_box.clear()
        self.partial_label.setText(
            "말을 시작하면 여기에 임시 인식 결과가 표시됩니다."
        )
        self.translation_error_label.setText("")
        self._last_final_text = ""
        self._overlay.clear_subtitles()

    def _set_controls_idle(self) -> None:
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.microphone_combo.setEnabled(True)
        self.refresh_button.setEnabled(True)
        self.screen_combo.setEnabled(True)

        for checkbox in self._language_checkboxes.values():
            checkbox.setEnabled(True)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API 이름 유지
        if self._speech_service.is_running:
            self._speech_service.stop()

        self._translation_service.shutdown()
        self._overlay.close()
        event.accept()
