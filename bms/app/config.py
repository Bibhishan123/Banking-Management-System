import os
from dataclasses import dataclass, asdict
from typing import Dict, Any

@dataclass
class Config:
    SQLALCHEMY_DATABASE_URI: str = os.getenv("BMS_DATABASE_URI", "sqlite:///db.sqlite")
    SQLALCHEMY_ECHO: bool = False
    DEBUG: bool = os.getenv("BMS_DEBUG", "0") == "1"
    BATCH_SIZE: int = int(os.getenv("BMS_BATCH_SIZE", "10"))
    SMTP_HOST: str = os.getenv("BMS_SMTP_HOST", "localhost")
    SMTP_PORT: int = int(os.getenv("BMS_SMTP_PORT", "1025"))
    SMTP_USER: str | None = os.getenv("BMS_SMTP_USER", None)
    SMTP_PASS: str | None = os.getenv("BMS_SMTP_PASS", None)
    LOG_JSON: bool = os.getenv("BMS_LOG_JSON", "0") == "1"

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def from_mapping(self, mapping: Dict[str, Any]) -> None:
        for k, v in mapping.items():
            if hasattr(self, k):
                setattr(self, k, v)
