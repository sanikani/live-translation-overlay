from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import requests
from PySide6.QtCore import QObject, Signal

from src.config.settings import Settings


class TranslationService(QObject):
    """Azure Translator 호출을 UI 스레드 밖에서 순차 처리한다."""

    translation_ready = Signal(str, str, str)
    status_changed = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="translator",
        )
        self._closed = False

    def translate_async(
        self,
        source_text: str,
        target_language: str = "en",
    ) -> None:
        text = source_text.strip()
        if not text or self._closed:
            return

        settings = Settings.from_env()
        if not settings.translator_configured:
            self.status_changed.emit("번역 설정 필요")
            return

        self.status_changed.emit("번역 중")
        self._executor.submit(
            self._translate,
            settings,
            text,
            target_language,
        )

    def _translate(
        self,
        settings: Settings,
        source_text: str,
        target_language: str,
    ) -> None:
        try:
            endpoint = settings.translator_endpoint.rstrip("/")
            url = f"{endpoint}/translate"

            params = {
                "api-version": "3.0",
                "from": "ko",
                "to": target_language,
            }

            headers = {
                "Ocp-Apim-Subscription-Key": settings.translator_key,
                "Content-Type": "application/json",
            }
            if settings.translator_region:
                headers["Ocp-Apim-Subscription-Region"] = settings.translator_region

            response = requests.post(
                url,
                params=params,
                headers=headers,
                json=[{"Text": source_text}],
                timeout=10,
            )
            response.raise_for_status()

            payload = response.json()
            translated_text = payload[0]["translations"][0]["text"].strip()

            self.translation_ready.emit(
                source_text,
                target_language,
                translated_text,
            )
            self.status_changed.emit("번역 준비됨")
        except requests.Timeout:
            self.error_occurred.emit(
                "번역 서버 응답이 늦어 이번 문장의 번역을 건너뛰었습니다."
            )
            self.status_changed.emit("번역 지연")
        except requests.RequestException as exc:
            self.error_occurred.emit(
                f"번역 요청에 실패했습니다. 음성 인식은 계속됩니다. ({exc})"
            )
            self.status_changed.emit("번역 오류")
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            self.error_occurred.emit(
                f"번역 결과를 읽지 못했습니다. 음성 인식은 계속됩니다. ({exc})"
            )
            self.status_changed.emit("번역 오류")

    def shutdown(self) -> None:
        if self._closed:
            return

        self._closed = True
        self._executor.shutdown(wait=False, cancel_futures=True)
