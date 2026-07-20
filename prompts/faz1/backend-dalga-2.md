# [BACKEND] Faz 1 · Dalga 2 — BE-5 + BE-2

Sen Radar projesinin **backend** ajanısın. `CLAUDE.md`'yi oku. Sadece `api/**` ve
`docs/openapi.yaml` altına yazarsın.

Önce `docs/TASKS.md` içindeki `## Bloke` → "Karara bağlananlar" bölümünü oku. Docker kararı
verildi: compose doğrulaması Faz 6'ya taşındı, bu turda `docker-compose.yml`'a dokunma.

İki görev var, sırayla, ayrı commit'ler. BE-5 küçük ve CI'ı kırmızıdan çıkarıyor — önce o.

---

## GÖREV BE-5 — CI'ı yeşile döndür

**Amaç:** Güvenlik ajanının `api/` içinde bulduğu iki lint/tip bulgusunu kapatmak.

**Oku:** `docs/REVIEW.md` (SEC-1-B1 ve SEC-1-B2 detayları), `docs/TASKS.md` `## Bloke`.

**Dokunabileceğin dosyalar:** `api/routes/health.py`, `api/config.py`

**Bulgular:**
- **SEC-1-B1** — `api/routes/health.py:22` ve `:34`, ruff `ASYNC109`: async fonksiyon
  `timeout` parametresi alıyor. Davranış doğru, üslup uyarısı. **Tercih edilen çözüm:**
  `timeout` parametresini kaldır, zaman aşımını çağıran tarafta `asyncio.timeout()` ile sar.
  Kuralı `ruff.toml`'da muaf tutmayı deneme — o dosya senin değil; muafiyet gerektiğine
  ikna olursan `## Bloke`'ya gerekçesiyle yaz ve BE-5'i bu maddeyle açık bırak.
- **SEC-1-B2** — `api/config.py:47`, mypy `unused-ignore`: gereksiz
  `# type: ignore[call-arg]`. Yorumu sil.

**Kabul kriterleri:**
- `ruff check .` sıfır hata.
- `mypy api/` sıfır hata.
- `pytest` hâlâ yeşil, 11 testin hepsi geçiyor — `/health` davranışı değişmedi:
  sağlıklı yol 200, db arızası 503, redis arızası 503, ikisi de arızalı 503.
- Zaman aşımı davranışı korunmuş: bir bağımlılık asılı kaldığında `/health` süresiz
  beklemiyor, hâlâ 503 dönüyor. Bunu doğrulayan test varsa geçiyor, yoksa davranışı elle
  doğrula ve kapanış notunda nasıl doğruladığını yaz.

**Kapanış:** `docs/TASKS.md`'de BE-5'i `## Biten` altına taşı ve `## Bloke` içindeki
SEC-1-B1/SEC-1-B2 satırlarının sonuna `→ BE-5 ile çözüldü` ekle. `git add api/ docs/TASKS.md`,
`be:` prefix'iyle commit'le.

---

## GÖREV BE-2 — veri modeli

**Amaç:** SPEC §3'teki altı tabloyu SQLAlchemy 2.0 modelleri ve ilk Alembic migration'ı
olarak yazmak.

**Oku:** `docs/SPEC.md` §3 (veri modeli, alan listeleri, `status` değerleri) ve §4
(triyaj skorunun üç alt skoru — `triage_scores` tablosu bunları ayrı ayrı saklar).

**Dokunabileceğin dosyalar:** `api/**` (modeller, migration dizini), `pyproject.toml`
(yeni bağımlılık gerekirse)

**Yapılacaklar:**
- Altı tablo: `businesses`, `snapshots`, `posts`, `triage_scores`, `audits`, `outreach`.
  Alanlar SPEC §3'te birebir listelenmiş — alan ekleme, çıkarma, yeniden adlandırma.
- SQLAlchemy 2.0 modern stil: `DeclarativeBase` + `Mapped[]` + `mapped_column()`.
  Legacy `Column()` kullanma.
- `status` alanları SPEC §3'teki değer kümeleriyle sınırlı: triyaj
  `qualified | watch | rejected`, erişim `draft | sent | opened | replied | meeting | won | lost`.
  Veritabanı seviyesinde zorla (native enum veya CHECK constraint — hangisini seçtiğini
  kapanış notunda gerekçelendir).
- `outreach.status` varsayılanı **`draft`** olmalı ve bu veritabanı varsayılanı olmalı.
  `CLAUDE.md` hukuki sınırlar: sistem hiçbir koşulda otomatik mesaj göndermez, kayıt `draft`
  doğar.
- `audits.llm_cost_usd` **NOT NULL**. `CLAUDE.md` maliyet disiplini: bu alan boş kalamaz.
  Para alanı `Numeric`, `Float` değil.
- Zaman alanları `TIMESTAMP WITH TIME ZONE`, UTC.
- Yabancı anahtarlar ve indeksler: `snapshots.business_id`, `posts.snapshot_id`,
  `triage_scores.business_id`, `audits.business_id`, `outreach.audit_id`. `businesses.place_id`
  ve `businesses.ig_handle` benzersiz (ig_handle nullable olabilir — SPEC'te eşleme sonradan
  oluyor).
- 180 günlük silme (`CLAUDE.md`) Faz 6'da cron olacak; şimdi **yazma**, ama silmenin
  dayanacağı zaman alanının (`businesses.discovered_at`) indeksli olduğundan emin ol.
- Tek Alembic migration: `upgrade()` ve `downgrade()` ikisi de dolu.

**Yapmayacakların:**
- Erişim, gösterim, kaydetme, profil ziyareti, demografi alanı ekleme (`CLAUDE.md` kural 7).
  `posts` tablosunda yalnızca SPEC §3'te yazan `like_count`, `comment_count`, `view_count` var.
- `docs/openapi.yaml`'a dokunma — bu turda yeni uç yok.

**Kabul kriterleri:**
- `alembic upgrade head` temiz bir veritabanında hatasız çalışıyor.
- `alembic downgrade base` ardından `alembic upgrade head` yine hatasız (migration geri
  alınabilir).
- `alembic check` (veya `alembic revision --autogenerate` sonrası boş diff) — modeller ile
  migration arasında sapma yok.
- `mypy api/` ve `ruff check .` sıfır hata.
- `pytest` yeşil.
- Doğrulama sorgusu: `outreach` tablosuna `status` vermeden satır eklenince değer `draft`
  oluyor; `audits` tablosuna `llm_cost_usd` vermeden satır eklemek **hata veriyor**.
- `git grep -nE "impressions|reach|saves|profile_views|demographics" -- api/` çıktısı boş.

**Kapanış:** `docs/TASKS.md`'de BE-2'yi `## Biten` altına tek satır sonuç notuyla taşı
(enum/CHECK tercihinin gerekçesini yaz). `git add api/ pyproject.toml docs/TASKS.md`,
`be:` prefix'iyle commit'le. Sonra dur — BE-4 hazır olduğunu orkestra şefine bildir.
