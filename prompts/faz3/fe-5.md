# [FRONTEND] Faz 3 · FE-5 — canlı done + gerçek skorlar (FE-4'ü kapat)

**BEKLET: BE-12 bitene kadar gönderme.** `/businesses` + `/stats` DB'den okumalı
(`docs/TASKS.md`'de BE-12 `## Biten`'de). BE-10 (worker fixture modu) zaten bitti.

---

Sen Radar projesinin **frontend** ajanısın. `CLAUDE.md`'yi oku. Sadece `web/**` ve
`docs/DESIGN.md` altına yazarsın. `api/**`'ye dokunmazsın (çalıştırmak serbest, yazmak değil).

## GÖREV FE-5 — Faz 3 panelini canlı doğrula, FE-4 done'u kapat

**Amaç:** BE-10 (worker fixture modu) + BE-12 (uçlar DB'den) sayesinde artık uçtan uca gerçek:
keşif başlat → job done → panel **gerçek skorlanmış ~100 hesabı** gösteriyor. FE-4'ün canlı
done doğrulamasını tamamla.

**Oku:** `docs/TASKS.md` `## Biten` → BE-10 (worker fixture modu nasıl açılır:
`RADAR_FIXTURE_MODE`), BE-11/BE-12 (skorlar DB'de, uçlar DB'den okuyor). `## Devam eden` → FE-4.
`docs/SPEC.md` §1/§4 (skor bantları, üç alt skor). Kendi FE-3/FE-4 çıktın.

**Dokunabileceğin dosyalar:** `web/**`, `docs/DESIGN.md`

**Yapılacaklar:**
- Backend'i **fixture modunda** ayağa kaldır (`RADAR_FIXTURE_MODE` açık): postgres + redis +
  migration + FastAPI + arq worker. (BE-10 kapanış notu yol gösterir.) Anahtar gerekmez, canlı
  çağrı yok (kural 6).
- Panelden keşif başlat → gerçek `job_id` → `queued→running→done` → tablo **gerçek DB
  verisiyle** (~100 hesap, skorlu) tazeleniyor. Bu, FE-4-B1 + FE-4-B2'nin birlikte kapandığının
  kanıtı.
- Skor bandının (FE-1'de kurduğun üç duraklı, renk-dışı ikinci işaretli skala) gerçek skorlarla
  doğru göründüğünü doğrula: `<40` elendi, `40–69` izlemede, `≥70` nitelikli. Kohort<5 →
  skor "—" + `watch` etiketi (FE-2'de kurduğun yol) gerçek veriyle çalışıyor.
- Üst şerit gerçek `/stats`: taranan ~100, nitelikli sayısı, rapor 0 (Faz 4), maliyet 0.
- Gerekiyorsa küçük UI düzeltmeleri (yalnız `web/`); yeni büyük özellik değil.

**Yapmayacakların:**
- `api/`'ye yazma; sorun görürsen `## Bloke`. Elle API tipi yazma (gen:api).
- Erişim/gösterim/kaydetme/demografi alanı gösterme (kural 7).
- Sabit URL, `#hex` (token dışı), sonsuz poll.

**Kabul kriterleri:**
- Fixture modunda gerçek backend'e karşı: keşif → done → tablo ~100 skorlu hesapla tazeleniyor;
  poll done'da duruyor; error dalı gösteriliyor. Headless/Network kanıtı kapanış notunda.
- Skor bantları üç durumu da gerçek veriyle doğru çiziyor; kohort<5 "—"+watch doğru.
- `npm run build` + `npx tsc --noEmit` + `npx next lint` sıfır hata.
- `git grep -nE "#[0-9a-fA-F]{6}" -- web/app web/components` boş; yasak-metrik grep boş.

**Kapanış:** `docs/TASKS.md`'de FE-4'ü `## Devam eden`'den ve FE-5'i `## Açık`'tan `## Biten`'e
taşı (ikisini tek satırla birleştirebilirsin: "FE-4 done canlı doğrulandı, FE-5 panel gerçek
skorları gösteriyor"). `docs/DESIGN.md` güncelle. `git add web/ docs/DESIGN.md docs/TASKS.md`,
`fe:` prefix'iyle commit'le. Sonra orkestra şefine "Faz 3 paneli canlı, gerçek skorlar
görünüyor" de.
