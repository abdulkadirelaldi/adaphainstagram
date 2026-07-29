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

    # Dış kaynak kimlik bilgileri (SPEC §2). Opsiyonel: yalnızca ilgili adaptör canlı
    # çağrı yaparken gerekir. Testler client enjekte ettiği için bunları okumaz; bu
    # yüzden zorunlu değiller (uygulama/testler anahtarsız da kurulur).
    google_places_api_key: str | None = Field(
        default=None, description="Google Places API (New) anahtarı."
    )
    ig_business_discovery_token: str | None = Field(
        default=None, description="IG Graph API Business Discovery erişim jetonu."
    )
    apify_token: str | None = Field(default=None, description="Apify API jetonu.")
    anthropic_api_key: str | None = Field(
        default=None, description="Anthropic API anahtarı (LLM katmanı, SPEC §6)."
    )
    # Üretilen denetim PDF'lerinin yazılacağı dizin (Faz 5). Yerel render, dış çağrı
    # değil (kural 6). Depo dışında/gitignore'lu tutulmalı.
    pdf_output_dir: str = Field(default="./var/audit_pdfs", description="Denetim PDF çıktı dizini.")

    # Hukuki sınır (CLAUDE.md): dönüşmeyen adayın verisi bu süre sonra silinir (cron,
    # opsiyonel değil). Varsayılan 180 gün — politika sabiti; test için ayarlanabilir.
    retention_days: int = Field(default=180, ge=1, description="Silme öncesi bekleme (gün).")
    # Aylık LLM maliyeti bu eşiği aşınca alarm (Stats.monthly_cost_alarm=true + log).
    # Alarm bir bildirim; sistemi durdurmaz. Tanımlı değilse alarm hep kapalı.
    monthly_cost_limit_usd: float | None = Field(
        default=None, ge=0, description="Aylık maliyet alarm eşiği (USD). Boşsa alarm kapalı."
    )
    # Rate limit (Faz 6 sertleştirme): ağır uçlarda dakika başına istemci-başına istek
    # sınırı. Aşılınca 429 + Retry-After. Redis sayacı; redis yoksa sınır uygulanmaz.
    rate_limit_per_minute: int = Field(
        default=30, ge=1, description="Ağır uçlarda istemci başına dakikalık istek sınırı."
    )

    # Maliyet disiplini (CLAUDE.md): aynı hesap 7 gün içinde tekrar kazınmaz. BE-9
    # profil çekmeden önce bu TTL'li Redis anahtarına bakar. Varsayılan 7 gün.
    snapshot_cache_ttl_seconds: int = Field(
        default=7 * 24 * 60 * 60, ge=1, description="Snapshot tazelik cache'i TTL (saniye)."
    )

    # Açıkken worker keşif job'u canlı API yerine tests/fixtures/ ile çalışır (kural 6).
    # ÜRETİMDE KAPALI olmalı — açık kalırsa sahte veri sunar. Yerel/test/CI'da açılır.
    radar_fixture_mode: bool = Field(
        default=False,
        description="Keşif job'unu fixture'la yürüt (canlı çağrı yok). Üretimde False.",
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


class CorsSettings(BaseSettings):
    """CORS origin'leri — uygulama **kurulurken** (create_app) gerekir.

    Ayrı bir ayar sınıfı olması bilinçli: ana `Settings` `database_url`/`redis_url`'ı
    zorunlu tutar (eksikse fail-fast), ama bunlar yalnızca çalışma anında (lifespan)
    gerekir. CORS ise middleware eklenirken, yani uygulama kurulurken lazım. İkisi
    aynı sınıfta olsaydı `create_app()` her çağrıda db/redis konfigürasyonu isterdi
    ve hermetik testler (canlı config olmadan uygulamayı kuran) kırılırdı. Bu sınıfın
    zorunlu alanı yok — güvenli varsayılana düşer, her ortamda kurulabilir.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    cors_allow_origins: str = Field(
        default="http://localhost:3000",
        description="CORS için izin verilen origin'ler, virgülle ayrılmış.",
    )

    def origins(self) -> list[str]:
        """Virgülle ayrılmış origin'leri temiz bir listeye çevirir.

        Boş/yalnızca boşluk token'lar atılır. Sonuç boşsa (ör. `.env`'de anahtar
        değersiz bırakılmışsa) varsayılan tek origin'e düşer — açık liste korunur,
        yanlışlıkla `["*"]`'a dönüşmez.
        """
        raw = [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]
        return raw or ["http://localhost:3000"]


@lru_cache
def get_cors_settings() -> CorsSettings:
    """CORS ayarını bir kez okur ve önbelleğe alır."""
    return CorsSettings()
