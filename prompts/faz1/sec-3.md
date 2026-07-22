# [GÜVENLİK & TEST] Faz 1 · SEC-3 — ruff konfig temizliği

Sen Radar projesinin **güvenlik & test** ajanısın. `CLAUDE.md`'yi oku. `ruff.toml` senin
sahipliğinde. Sadece `ruff.toml`, `docs/REVIEW.md`, `tests/**` altına yazarsın.

## GÖREV SEC-3 — iki ruff bloğunu kapat

**Amaç:** `## Bloke` içindeki BE-2-B1'i çözmek ve UP042 kararını uygulamak.

**Oku:** `docs/TASKS.md` `## Bloke` → BE-2-B1 ve UP042 satırları, "Karara bağlananlar" notu.

**Dokunabileceğin dosyalar:** `ruff.toml`, `docs/REVIEW.md`, `tests/**`

**Yapılacaklar:**
- **BE-2-B1 (kritik):** `ruff.toml`'daki `extend-exclude` yolu `migrations/versions` migration
  dizinine uymuyor; gerçek yol `api/migrations/versions`. Exclude'u gerçek yola çevir ki
  gelecekte autogenerate edilen her migration lint gürültüsü yapmasın. Yalnızca `versions/`
  dizini (Alembic'in ürettiği) dışlanmalı — `env.py` gibi elle yazılan migration altyapısı
  lint kapsamında kalmalı.
- **UP042 (karar verildi — uygulama):** orkestra şefi ruff pin'ini **yükseltmeme** kararı
  verdi. CI 0.12.0'da sabit kalır; `schemas.py` `StrEnum` düzeltmesi ileride pin çıkınca
  yapılır. Yapılacak tek şey: bu kararı `docs/REVIEW.md`'de UP042 bulgusunun yanına
  "ertelendi, ruff pin 0.12.0'da sabit" olarak yaz. `ruff.toml`'da UP042'yi **kalıcı olarak
  susturma** (`ignore`'a ekleme) — pin çıkınca gerçekten düzeltilecek, susturulmayacak.

**Kabul kriterleri:**
- `ruff check .` yeşil (mevcut migration dahil).
- Yeni bir dosya `api/migrations/versions/` altına konursa (elle bir dummy dosyayla test et,
  sonra sil) ruff onu **atlıyor**; ama `api/migrations/env.py` **lint'leniyor**. İkisini de
  doğrula, kapanış notuna yaz.
- `ruff.toml`'da `UP042` `ignore`/`extend-ignore` listesinde **değil** (susturulmadı, ertelendi).
- `pytest` hâlâ yeşil (22/22 veya güncel sayı).
- `docs/REVIEW.md`: BE-2-B1 `PASS`'a çevrildi (kanıt satırıyla), UP042 "ertelendi" notu eklendi.

**Kapanış:** `docs/TASKS.md`'de SEC-3'ü `## Biten` altına taşı; `## Bloke` içindeki BE-2-B1 ve
UP042 satırlarının sonuna `→ SEC-3` ekle. `git add ruff.toml docs/REVIEW.md tests/
docs/TASKS.md`, `sec:` prefix'iyle commit'le.
