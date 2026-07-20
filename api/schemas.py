"""HTTP yanıt şemaları.

Bu modül `docs/openapi.yaml` sözleşmesinin Python karşılığıdır. Sözleşme kaynaktır:
buradaki bir alan değişecekse önce o dosya güncellenir (CLAUDE.md kural 3).
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict


class ComponentStatus(str, Enum):
    """Tek bir bileşenin sağlık durumu."""

    OK = "ok"
    ERROR = "error"


class Health(BaseModel):
    """`GET /health` yanıtı."""

    model_config = ConfigDict(extra="forbid")

    status: ComponentStatus
    db: ComponentStatus
    redis: ComponentStatus

    @property
    def is_healthy(self) -> bool:
        return self.status is ComponentStatus.OK
