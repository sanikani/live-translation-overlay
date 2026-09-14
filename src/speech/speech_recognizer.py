from __future__ import annotations

from typing import Optional

import azure.cognitiveservices.speech as speechsdk
from PySide6.QtCore import QObject, Signal

from src.config.settings import Settings


class SpeechRecognitionService(QObject):
    """Azure Speech SDK의 콜백을 Qt Signal로 변환하는 얇은 서비스 계층."""

    partial_text = Signal(str)
    final_text = Signal(str)
    status_changed = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._recognizer: Optional[speechsdk.SpeechRecognizer] = None
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self, microphone_name: Optional[str] = None) -> None:
        if self._running:
            return

        settings = Settings.from_env()
        if not settings.is_configured:
            self.error_occurred.emit(
                "Azure Speech 설정이 없습니다. .env 파일에 "
                "AZURE_SPEECH_KEY와 AZURE_SPEECH_REGION을 입력해 주세요."
            )
            return

        try:
            speech_config = speechsdk.SpeechConfig(
                subscription=settings.speech_key,
                region=settings.speech_region,
            )
            speech_config.speech_recognition_language = settings.speech_language

            if microphone_name:
                audio_config = speechsdk.audio.AudioConfig(device_name=microphone_name)
            else:
                audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

            recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config,
                audio_config=audio_config,
            )

            recognizer.recognizing.connect(self._on_recognizing)
            recognizer.recognized.connect(self._on_recognized)
            recognizer.canceled.connect(self._on_canceled)
            recognizer.session_started.connect(self._on_session_started)
            recognizer.session_stopped.connect(self._on_session_stopped)

            # 콜백은 별도 스레드에서 빠르게 호출될 수 있으므로
            # 인식 시작 요청 전에 상태를 먼저 설정한다.
            self._recognizer = recognizer
            self._running = True

            recognizer.start_continuous_recognition_async().get()

            if self._running:
                self.status_changed.emit("듣는 중")
        except Exception as exc:  # SDK/장치 초기화 실패를 사용자 메시지로 변환
            self._recognizer = None
            self._running = False
            self.error_occurred.emit(f"음성 인식을 시작하지 못했습니다.\n{exc}")

    def stop(self) -> None:
        recognizer = self._recognizer
        if recognizer is None:
            self._running = False
            self.status_changed.emit("대기 중")
            return

        try:
            recognizer.stop_continuous_recognition_async().get()
        except Exception as exc:
            self.error_occurred.emit(f"음성 인식을 종료하는 중 오류가 발생했습니다.\n{exc}")
        finally:
            self._recognizer = None
            self._running = False
            self.partial_text.emit("")
            self.status_changed.emit("대기 중")

    def _on_recognizing(self, evt: speechsdk.SpeechRecognitionEventArgs) -> None:
        text = (evt.result.text or "").strip()
        if text:
            self.partial_text.emit(text)

    def _on_recognized(self, evt: speechsdk.SpeechRecognitionEventArgs) -> None:
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            text = (evt.result.text or "").strip()
            if text:
                self.final_text.emit(text)
                self.partial_text.emit("")

    def _on_canceled(self, evt: speechsdk.SpeechRecognitionCanceledEventArgs) -> None:
        self._running = False

        details = getattr(evt, "error_details", "") or ""
        if details:
            self.error_occurred.emit(f"음성 인식이 중단되었습니다.\n{details}")
        else:
            self.error_occurred.emit("음성 인식이 중단되었습니다.")

        self.status_changed.emit("중단됨")

    def _on_session_started(self, _evt: object) -> None:
        self.status_changed.emit("듣는 중")

    def _on_session_stopped(self, _evt: object) -> None:
        if self._running:
            self._running = False
            self.status_changed.emit("중단됨")
