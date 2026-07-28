# [FRONTEND] Faz 5 · FE-7 — PDF indir + outreach durum takibi + taslak kopyala

Sen Radar projesinin **frontend** ajanısın. `CLAUDE.md`'yi oku (hukuki sınır: sistem otomatik
mesaj göndermez — arayüz **gönderme düğmesi sunmaz**, yalnız taslak + kopyala + durum kaydı).
Sadece `web/**` ve `docs/DESIGN.md` altına yazarsın.

## GÖREV FE-7 — çıktı arayüzü

**Amaç:** Rapor PDF'ini indirtmek, erişim taslağını kopyalatmak ve outreach durumunu insanın
elle güncellemesini sağlamak. Sözleşme (BE-17) donmuş.

**Oku:** `docs/openapi.yaml` (BE-17: `GET /audits/{id}/pdf`, `PATCH /outreach/{id}`, `Outreach`
şeması, durum enum). SPEC §7, §3 (durum kümesi). `docs/TASKS.md` `## Biten` → BE-18/BE-19
(canlı davranış: PDF-yok 409, geçersiz durum 422). Kendi FE-6 çıktın (rapor görünümü + kopyala).

**Dokunabileceğin dosyalar:** `web/**`, `docs/DESIGN.md`

**Yapılacaklar:**
- **Tip yenileme:** `npm run gen:api` ile yeni uç/şema tipleri.
- **PDF indir:** rapor görünümünde "PDF indir" düğmesi → `GET /audits/{id}/pdf` (binary,
  `application/pdf`). PDF henüz üretilmemişse (409) düğme pasif/bekliyor durumu, sebebi belli.
- **Outreach durum takibi:** kaydın durumunu göster (`draft…lost`) ve insan **elle** değiştirsin
  → `PATCH /outreach/{id}`. Durumlar tek bakışta okunur (renk tek taşıyıcı değil). Geçersiz
  değer 422 dönerse kullanıcıya net hata.
- **Taslak kopyala:** erişim mesajı taslağı kopyalanabilir (FE-6'da kurdun, pekiştir).
- **DESIGN.md:** PDF indirme durumu, outreach durum takibi yerleşimi, boş/yükleniyor/hata.

**Yapmayacakların:**
- **Mesaj GÖNDEREN hiçbir UI.** "Gönder", "DM at", "e-posta yolla" yok — yalnız taslak + kopyala
  + durum *kaydı* (CLAUDE.md hukuki sınır). Durum güncelleme bir insan eylemidir, mesaj gönderimi
  değil.
- `openapi.yaml` düzenleme; elle tip yazma (gen:api). Sorun → `## Bloke`.
- Erişim/gösterim/kaydetme/demografi gösterme (kural 7). Sabit URL, token dışı `#hex`.

**Kabul kriterleri:**
- `gen:api` + `npm run build` + `npx tsc --noEmit` + `npx next lint` sıfır hata.
- Canlı (BE-18/BE-19 ayakta, fixture modu): PDF indirilebiliyor (üretilmişse), 409'da düğme
  pasif; outreach durumu değiştirilip `PATCH` gönderiliyor ve panelde güncelleniyor; geçersiz
  değer hatası gösteriliyor. Headless/Network kanıtı kapanış notunda.
- `git grep -niE "gönder|send|dm at|e-posta|email.*send" -- web/` yalnız "taslak/kopyala/durum"
  bağlamında; mesaj gönderen kod yok.
- `git grep -nE "#[0-9a-fA-F]{6}" -- web/app web/components` boş; yasak-metrik grep boş.
- **BE-18/BE-19 canlı değilken:** UI + tip + istekler hazır; canlı doğrulama onlar ayağa
  kalkınca → o zamana dek `## Devam eden`'de bırak.

**Kapanış:** Canlı doğrulama tamsa `## Biten`'e (Faz 5 kutu #2 "taslak kopyalanabiliyor" + PDF
indirme), değilse `## Devam eden`'e. `docs/DESIGN.md` güncelle. `git add web/ docs/DESIGN.md
docs/TASKS.md`, `fe:` commit.
