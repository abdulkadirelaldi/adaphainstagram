# [GÜVENLİK & TEST] Faz 3 · SEC-7 — skorlama motorunu bağımsız doğrula

**BEKLET: BE-11 bitene kadar gönderme.** `docs/TASKS.md`'de BE-11 `## Biten`'e taşınmış ve
skorlama saf fonksiyonları + `triage_scores` persist'i yazılmış olmalı.

---

Sen Radar projesinin **güvenlik & test** ajanısın. `CLAUDE.md`'yi oku. Sadece `tests/**`,
`.github/**`, `docs/REVIEW.md` ve lint konfig dosyalarına yazarsın. `api/**`'ye dokunmazsın —
bulgu `## Bloke`'ya.

## GÖREV SEC-7 — triyaj skorlama testleri

**Amaç:** BE-11'in skorlama iddialarını (çarpım çökme, kohort<5→watch, eşikler, mutlak-eşik
yokluğu, referans zaman) backend'in elle doğrulamasından bağımsız olarak makineye bağlamak.

**Oku:** `docs/SPEC.md` §4 ve §1, `docs/TASKS.md` `## Biten` → BE-11 (potansiyel kaç sinyal,
kararlar). `tests/fixtures/README.md` (`REFERENCE_NOW`, bant hedefleri). BE-11'in skorlama
fonksiyonlarını **oku**.

**Dokunabileceğin dosyalar:** `tests/**`, `docs/REVIEW.md`

**Yapılacaklar (her biri kalıcı test):**
- **Çarpım çökme davranışı:** aktiflik≈0 ama potansiyel/kapasite yüksek bir hesap birleşikte
  **düşük** (qualified değil). Toplam olsaydı yüksek çıkardı — çarpımın SPEC §4 gerekçesi.
  Karşı-kanıt: formülü toplama çevirince test kırmızıya döner (kodu bozma, testin ölçtüğünü
  anlat).
- **Kohort<5 → watch:** florist/gift_shop/pet_store (SEC-8'in <5 kategorileri) potansiyel
  hesaplanmadan `watch`. Kohort ≥5 kategoride potansiyel hesaplanıyor.
- **Durum eşikleri:** 39/40, 69/70 sınırlarında doğru bant (`rejected`/`watch`/`qualified`).
  Sınır değerlerini tam test et (off-by-one).
- **Mutlak eşik yokluğu:** aynı ham etkileşim değeri **farklı kategori medyanlarında** farklı
  potansiyel üretiyor — karşılaştırma kohort-göreli, mutlak değil (SPEC §4). Bunu gösteren test.
- **Referans zaman:** aktiflik `REFERENCE_NOW`'a göre; sabit fixture tarihleriyle deterministik.
  Testler `currentDate`'e bağlı değil (kural 6). Referans kaydırılınca aktiflik beklenen yönde
  değişiyor.
- **Persist:** `triage_scores` satırı alt skorlar + birleşik + status + `computed_at` taşıyor;
  BE-11'in idempotent semantiği (tekrar skorlama) test ediliyor.

**Kabul kriterleri:**
- Yukarıdaki testler `tests/`'te; `pytest` yeşil, ağ kapalıyken de yeşil.
- Çarpım ve mutlak-eşik testleri gerçekten ölçüyor (karşı-kanıt kapanış notunda).
- Skor sayıları fixture'dan türetiliyor (SEC-8'in `_fixture_facts` deseni) — magic number yok.
- Yeni bulgu varsa `## Bloke`'ya sahibiyle.

**Kapanış:** `docs/TASKS.md`'de SEC-7'yi `## Biten`'e taşı. `git add tests/ .github/
docs/REVIEW.md docs/TASKS.md`, `sec:` prefix'iyle commit'le.
