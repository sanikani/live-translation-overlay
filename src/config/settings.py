from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    speech_key: str
    speech_region: str
    speech_language: str = "ko-KR"

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()

        return cls(
            speech_key=os.getenv("AZURE_SPEECH_KEY", "").strip(),
            speech_region=os.getenv("AZURE_SPEECH_REGION", "").strip(),
            speech_language=os.getenv("AZURE_SPEECH_LANGUAGE", "ko-KR").strip() or "ko-KR",
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.speech_key and self.speech_region)
