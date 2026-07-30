# [GÜVENLİK & TEST] Faz 6 · SEC-13 — remote push + Actions yeşilini doğrula

**ÖN KOŞUL:** repoda bir `origin` remote'u kurulu olmalı (kullanıcı GitHub reposu açıp
`git remote add origin …` yapmış olmalı). `git remote -v` origin göstermiyorsa **başlama** —
`docs/TASKS.md` `## Bloke`'ya "remote yok" yazıp dur.

---

Sen Radar projesinin **güvenlik & test** ajanısın. `CLAUDE.md`'yi oku. `.github/` + CI senin
alanın; bu görev CI'ın gerçek GitHub Actions'ta koştuğunu doğrulamak.

## GÖREV SEC-13 — CI kutusunu gerçek Actions yeşiliyle kapat

**Amaç:** Şimdiye kadar "yerel + belgeli daraltma" olan CI kutularını (Faz 1 CI + Faz 6 e2e-CI)
gerçek GitHub Actions koşusuyla doğrulamak.

**Oku:** `.github/workflows/ci.yml` (mevcut — 3 job: ruff/mypy/pytest, servis konteyneri, e2e+
chromium). `docs/TASKS.md` `## Bloke` → "Karara bağlananlar" (CI/Docker daraltma notları).

**Dokunabileceğin dosyalar:** `.github/**`, `docs/REVIEW.md`, `docs/TASKS.md` (kendi satırın +
CI kutusu notu). **Kod dizinlerine (`api/`, `web/`) dokunma.**

**Yapılacaklar:**
1. **Push:** `git push -u origin master` (veya default branch neyse) — tüm ajanların commit'leri
   (be:/fe:/sec:/docs:) zaten atılmış, sadece gönderiliyor. `git add`/yeni commit gerekmez.
2. **Actions'ı izle:** push CI'ı tetikler. `gh run watch` / `gh run list --limit 1` (gh CLI
   varsa) ya da repo Actions sekmesinden koşuyu izle. Üç job da geçmeli:
   - ruff + ruff format
   - mypy
   - pytest (postgres 16 + redis 7 servis konteyneri + `playwright install chromium` → PDF/e2e
     testleri **SKIP değil koşuyor**)
3. **Yeşil değilse:** ci.yml'de ortam-farkı kaynaklı bir hata varsa (yerel geçip CI'da patlayan)
   düzelt (yalnız `.github/`), tekrar push. Hata `api/`/`web/` kaynaklıysa **düzeltme** —
   `## Bloke`'ya sahibiyle yaz.

**Kabul kriterleri:**
- Actions koşusu **yeşil**: üç job da geçti; PDF/e2e testleri CI'da gerçekten koştu (SKIP değil).
- `docs/REVIEW.md`'ye Actions run URL'si + üç job'un yeşil kanıtı yazıldı.
- CI'da patlayıp yerelde geçen bir fark varsa: ya `.github/` düzeltmesiyle kapatıldı ya da
  `## Bloke`'da sahibine yazıldı.

**Kapanış:** `docs/TASKS.md`'de SEC-13'ü `## Biten`'e taşı. **Aktif faz** başlığındaki ve
`## Bloke` "Karara bağlananlar"daki CI daraltma notlarını "→ SEC-13 ile gerçek Actions yeşili
alındı" olarak güncelle (Docker kutusu daraltılmış kalır — Docker kurulmadı). `git add .github/
docs/REVIEW.md docs/TASKS.md`, `sec:` commit ve push. Sonra "SEC-13 bitti, CI gerçek Actions'ta
yeşil" de.
