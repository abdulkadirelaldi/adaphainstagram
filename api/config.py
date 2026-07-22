"""Uygulama ayarları.

Tüm yapılandırma ortam değişkenlerinden okunur. Hiçbir sır koda gömülmez
(CLAUDE.md kural 4); yeni bir anahtar eklendiğinde `.env.example` da güncellenir.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(
        default="development",
        description="Çalışma ortamı: development | production",
    )

    database_url: str = Field(
        description="PostgreSQL bağlantı adresi, asyncpg sürücüsüyle.",
    )
    redis_url: str = Field(
        description="Redis bağlantı adresi. Hem cache hem arq kuyruğu bunu kullanır.",
    )

    db_pool_size: int = Field(default=5, ge=1)
    health_timeout_seconds: float = Field(
        default=3.0,
        gt=0,
        description=(
            "/health içindeki tek bir bağımlılık yoklamasının üst sınırı. Erişilemeyen "
            "bir bağımlılık, yanıtı belirsiz süre bekletmek yerine bu süre sonunda "
            "'error' olarak raporlanır."
        ),
    )


@lru_cache
def get_settings() -> Settings:
    """Ayarları bir kez okur ve önbelleğe alır."""
    # Alanlar ortamdan doldurulur; pydantic.mypy eklentisi bunu bildiği için
    # call-arg bastırması gerekmiyor.
    return Settings()
