from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import requests
from PySide6.QtCore import QObject, Signal

from src.config.settings import Settings


class TranslationService(QObject):
    """Azure Translator 호출을 UI 스레드 밖에서 순차 처리한다."""

    translation_ready = Signal(str, object)
    status_changed = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="translator",
        )
        self._closed = False

    def translate_many_async(
        self,
        source_text: str,
        target_languages: list[str],
    ) -> None:
        text = source_text.strip()
        targets = [code for code in dict.fromkeys(target_languages) if code]

        if not text or not targets or self._closed:
            return

        settings = Settings.from_env()
        if not settings.translator_configured:
            self.status_changed.emit("번역 설정 필요")
            return

        self.status_changed.emit("번역 중")
        self._executor.submit(
            self._translate_many,
            settings,
            text,
            targets,
        )

    def _translate_many(
        self,
        settings: Settings,
        source_text: str,
        target_languages: list[str],
    ) -> None:
        try:
            endpoint = settings.translator_endpoint.rstrip("/")
            url = f"{endpoint}/translate"

            params: list[tuple[str, str]] = [
                ("api-version", "3.0"),
                ("from", "ko"),
            ]
            params.extend(("to", language) for language in target_languages)

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
            translation_items = payload[0]["translations"]

            translations: dict[str, str] = {}
            for item in translation_items:
                language = str(item.get("to", "")).strip()
                translated_text = str(item.get("text", "")).strip()
                if language and translated_text:
                    translations[language] = translated_text

            if not translations:
                raise ValueError("번역 결과가 비어 있습니다.")

            self.translation_ready.emit(source_text, translations)

            missing = [
                language
                for language in target_languages
                if language not in translations
            ]
            if missing:
                self.error_occurred.emit(
                    "일부 언어의 번역 결과를 받지 못했습니다: "
                    + ", ".join(missing)
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
