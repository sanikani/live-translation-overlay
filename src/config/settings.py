from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    speech_key: str
    speech_region: str
    speech_language: str = "ko-KR"

    translator_key: str = ""
    translator_region: str = ""
    translator_endpoint: str = "https://api.cognitive.microsofttranslator.com"

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()

        return cls(
            speech_key=os.getenv("AZURE_SPEECH_KEY", "").strip(),
            speech_region=os.getenv("AZURE_SPEECH_REGION", "").strip(),
            speech_language=os.getenv("AZURE_SPEECH_LANGUAGE", "ko-KR").strip() or "ko-KR",
            translator_key=os.getenv("AZURE_TRANSLATOR_KEY", "").strip(),
            translator_region=os.getenv("AZURE_TRANSLATOR_REGION", "").strip(),
            translator_endpoint=(
                os.getenv(
                    "AZURE_TRANSLATOR_ENDPOINT",
                    "https://api.cognitive.microsofttranslator.com",
                ).strip()
                or "https://api.cognitive.microsofttranslator.com"
            ),
        )

    @property
    def is_configured(self) -> bool:
        """기존 Phase 1 코드와의 호환을 위해 Speech 설정 여부를 반환한다."""
        return self.speech_configured

    @property
    def speech_configured(self) -> bool:
        return bool(self.speech_key and self.speech_region)

    @property
    def translator_configured(self) -> bool:
        return bool(self.translator_key and self.translator_endpoint)
