# [BACKEND] Faz 3 · Dalga 7 — BE-11 (skorlama motoru) + BE-12 (uçları DB'ye bağla)

Sen Radar projesinin **backend** ajanısın. `CLAUDE.md`'yi oku (özellikle kural 6, 7 ve
"Faz 3 skorlama **LLM yok**" — SPEC §8). Sadece `api/**`, `docs/openapi.yaml` altına yazarsın.
İki görev, sırayla, ayrı commit'ler.

Bu görev Faz 3'ün dört çıkış kutusundan üçünü kapatıyor.

---

## GÖREV BE-11 — triyaj skorlama motoru

**Amaç:** SPEC §4'teki üç alt skoru, kohort medyanını, ağırlıklı çarpım birleşik skorunu ve
durum atamasını hesaplayıp `triage_scores`'a yazmak; skorlamayı discovery job'una tetikleme
fazı olarak bağlamak. **LLM yok, deterministik.**

**Oku:** `docs/SPEC.md` §4 (skorun tamamı — bu görevin sözleşmesi), §1 (durum eşikleri),
§3 (`triage_scores` alanları), §7 ("ölçmediğini iddia etme"). `tests/fixtures/README.md` →
**`REFERENCE_NOW=2026-07-15`** ve skor-bandı hedefleri (SEC-8 sözleşmesi). BE-9'un
`run_discovery` akışı (tetikleme fazını buraya ekleyeceksin).

**Dokunabileceğin dosyalar:** `api/**`

**Yapılacaklar:**

### Alt skorlar (her biri 0–100, saf fonksiyonlar)
- **Aktiflik:** son 90 gün gönderi sayısı + en uzun sessizlik. 0 gönderi → 0; haftada 2+
  gönderi ve <14 gün en uzun sessizlik → 100. "90 gün" ve "şimdi" penceresi **enjekte edilen
  referans zamandan** hesaplanır (üretimde `now`, testte `REFERENCE_NOW`). `datetime.now()`'ı
  fonksiyona gömme — referansı parametre al.
- **Potansiyel:** SPEC §4 dört sinyalin ortalaması der; **veri gerçeği:**
  - *Reels oranı düşüklüğü* — `posts.media_type` dağılımından.
  - *Etkileşim düşüklüğü* — (like+comment)/followers gibi bir oran, **aynı kategorideki
    taranmış hesapların medyanına göre** (mutlak eşik **YASAK**, SPEC §4). Kohort<5 → aşağıya bak.
  - *CTA yokluğu* — caption'da CTA var mı, **deterministik** tespit (anahtar kelime/regex:
    "dm", "ara", "sipariş", "link", "whatsapp" vb.). Faz 3 LLM kullanamaz; nitelikli CTA
    tespiti Faz 4 Haiku'nun işi, burada basit tespit yeterli.
  - *Yorum yanıt oranı düşüklüğü* — **bu veri sistemde yok.** `posts` yalnız `comment_count`
    taşır; yorum-düzeyi "kim yanıtladı" verisi Faz 2'de çekilmedi (SPEC §3 modelinde yok).
    **Karar (kural 7 — ölçmediğini iddia etme):** bu sinyali Faz 3'te **skora sokma**;
    potansiyel, ölçülebilen sinyallerin ortalaması olsun. Yorum yanıt sinyali Faz 4'te Apify
    yorum çekimi gelince eklenir. Bu kararı kod yorumunda ve kapanış notunda açıkça belgele —
    "dört sinyal" yerine kaç sinyal kullandığını yaz.
- **Kapasite:** kategori ağırlığı (klinik/kuyumcu/oto galeri/emlak yüksek; hobi/kişisel düşük —
  bir kategori→ağırlık haritası; fixture kategorileriyle eşleştir, bilinmeyen kategori nötr),
  takipçi eşiği, website varlığı, `businesses.rating_count`.

### Kohort medyanı (iki geçişli — kritik)
- Etkileşim karşılaştırması izole tek hesapla yapılamaz. Skorlama **batch**: önce her kategori
  için taranmış hesapların etkileşim **medyanını** hesapla, sonra her hesabı bu medyana göre
  skorla.
- **Kohort<5 hesap → potansiyel hesaplanmaz, hesap `watch`** (SPEC §4). Bu hesap için birleşik
  skor üretme; `triage_scores`'a `status=watch` ve potansiyel null (veya SPEC §3 alanına uygun
  bir işaret) yaz.

### Birleşik skor + durum
- `score = 100 * (activity/100)^0.30 * (potential/100)^0.40 * (capacity/100)^0.30` (SPEC §4).
  Ağırlıklı **çarpım** — toplam değil; herhangi bir alt skor 0'a yaklaşınca birleşik çöker.
- Durum: `<40 rejected`, `40–69 watch`, `≥70 qualified` (SPEC §1). Kohort<5 zaten watch.
- `triage_scores` satırı: alt skorlar + birleşik + status + `computed_at`. Aynı
  snapshot/business için idempotent (tekrar skorlama çift satır üretmesin ya da net bir
  "en güncel" semantiği olsun — hangisini seçtiğini belgele).

### Tetikleme
- `run_discovery`'nin **snapshot yazımından sonraki son fazı** olarak skorlamayı çağır
  (TASKS "Triyaj tetikleme kararı"). Fixture modunda (BE-10) job `done` olduğunda DB'de
  skorlanmış işletmeler durmalı.

**Yapmayacakların:**
- LLM çağrısı (Faz 3 yasak). Erişim/gösterim/demografi veya yorum-yanıt uydurma (kural 7).
- Mutlak etkileşim eşiği (SPEC §4 açıkça yasaklıyor). `datetime.now()`'ı skorlama saf
  fonksiyonuna gömme.

**Kabul kriterleri:**
- Skorlama saf fonksiyonları `REFERENCE_NOW` ile 100-hesap fixture'ında çalışıyor; skorlar
  README'deki bant hedeflerine yakın dağılıyor (rejected/watch/qualified hepsi mevcut).
- **Çarpım çökme davranışı doğrulandı:** bir alt skoru 0'a yakın hesap birleşikte düşük
  (ölü-ama-potansiyelli hesap qualified olmuyor — SPEC §4 gerekçesi).
- **Kohort<5 kategorisi (florist/gift_shop/pet_store) `watch`** — potansiyel hesaplanmıyor.
- Fixture modunda `discovery/run` job'u `done` olunca `triage_scores` dolu; ~100 hesap skorlu.
- `ruff` + `mypy api/` + `pytest` yeşil (CI pin'leri).
- `git grep -nE "impressions|reach|saves|profile_views|demographics" -- api/` boş.

**Kapanış:** `docs/TASKS.md`'de BE-11'i `## Biten`'e taşı (potansiyel kaç sinyal, kohort/çarpım
gerekçesi, idempotent semantiği). Faz 3 kutusu #1, #2 ve #4'ü işaretle (panel #3 BE-12'de).
`git add api/ docs/TASKS.md`, `be:` prefix'iyle commit'le.

---

## GÖREV BE-12 — `/businesses` + `/stats`'ı DB'ye bağla (FE-4-B1)

**Amaç:** İki ucu Faz 1'in `fake_data`'sından gerçek DB'ye geçirmek; son triyaj skorunu/durumunu
göstermek.

**Oku:** `docs/openapi.yaml` (`/businesses`, `/stats`, `Business`, `Stats` şemaları —
**değişmez**, sözleşme sabit; eksik görürsen önce ayrı commit'le güncelle, kural 3).
`docs/TASKS.md` `## Bloke` → FE-4-B1. BE-11'in `triage_scores` yazımı.

**Dokunabileceğin dosyalar:** `api/**`, `docs/openapi.yaml` (yalnız sözleşme eksikse)

**Yapılacaklar:**
- `GET /businesses`: `fake_data` yerine DB. `businesses` + **son** `triage_scores` join;
  `score`/`status` oradan. Filtreler (`status`/`category`/`min_score`) ve sayfalama
  (`limit`/`offset`, `total`) DB sorgusunda uygulanır. Skoru olmayan (henüz skorlanmamış /
  kohort<5) hesap için `score`/`status`'un sözleşmedeki nullable davranışına uy.
- `GET /stats`: DB'den — `scanned` (taranmış işletme), `qualified` (status=qualified sayısı),
  `reports` (audits — Faz 4, şimdilik 0), `monthly_cost_usd` (`audits.llm_cost_usd` toplamı —
  şimdilik 0). Uydurma sayı döndürme; gerçek sorgu, boş tablo → 0.
- `fake_data` artık üretim yolunda kullanılmıyor; sil ya da yalnız teste bırak (hangisi olduğunu
  belirt).

**Kabul kriterleri:**
- Fixture modunda `discovery/run` + skorlama sonrası: `GET /businesses` **DB'den ~100 gerçek
  işletmeyi** skorlarıyla döndürüyor (eski 8 sahte kayıt **yok**); `GET /stats` gerçek sayıları.
- Filtreler/sayfalama DB'de çalışıyor: `status=qualified` yalnız nitelikli, `min_score=70`
  eşik üstü, boş sonuç mümkün.
- Üretilen `/openapi.json` sözleşmeyle hâlâ uyumlu; yasak alan yok.
- `ruff` + `mypy api/` + `pytest` yeşil.

**Kapanış:** `docs/TASKS.md`'de BE-12'yi `## Biten`'e taşı, `## Bloke` FE-4-B1 satırına
`→ BE-12 ile çözüldü` ekle. Faz 3 kutusu #3'ü işaretle. `git add api/ docs/openapi.yaml
docs/TASKS.md`, `be:` prefix'iyle commit'le. Sonra orkestra şefine "BE-11+BE-12 bitti; SEC-7
skorlamayı test edebilir, FE-5 canlı done + gerçek skorları doğrulayabilir" de.
