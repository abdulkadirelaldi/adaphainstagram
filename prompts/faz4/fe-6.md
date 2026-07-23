# [FRONTEND] Faz 4 · FE-6 — audit tetikleme + rapor görünümü + outreach draft

Sen Radar projesinin **frontend** ajanısın. `CLAUDE.md`'yi oku. Sadece `web/**` ve
`docs/DESIGN.md` altına yazarsın. `api/**`, `docs/openapi.yaml`, `tests/**`'e dokunmazsın —
sorun görürsen `## Bloke`'ya.

## GÖREV FE-6 — denetim akışı arayüzü

**Amaç:** Nitelikli bir hesap için derin denetimi tetikleyen, sonucu (bulgu listesi + görünürlük
skoru + rapor metni) gösteren ve erişim mesajı taslağını kopyalatan arayüz. Sözleşme (BE-13)
donmuş; tipleri ondan üret.

**Oku:** `docs/openapi.yaml` — BE-13'ün `POST /businesses/{id}/audit`, `GET /audits/{id}`,
`Finding`, `Audit` şemaları. SPEC §5 (bulgu önemleri: kritik/yüksek/orta/düşük — panelde
önceliklendirme), §7, §1 (yalnız `qualified` hesap denetlenir — buton yalnız onlarda aktif).
`docs/TASKS.md` → "Faz 4 karara bağlananlar" (5 kural üretilir, 2'si değil — panel eksik
bulguyu "hata" gibi göstermesin). Kendi FE-4/FE-5 çıktın.

**Dokunabileceğin dosyalar:** `web/**`, `docs/DESIGN.md`

**Yapılacaklar:**
- **Tip yenileme:** `npm run gen:api` ile yeni uç/şema tipleri.
- **Audit tetikleme:** yalnız `qualified` hesapta aktif "Derin denetim" düğmesi →
  `POST /businesses/{id}/audit` → `job_id` → `/jobs/{id}` yoklama (FE-4'ün poll desenini yeniden
  kullan, kopyalama). Nitelikli olmayan hesapta düğme pasif/gizli, sebebi belli.
- **Rapor görünümü:** iş bitince `GET /audits/{id}` → görünürlük skoru + bulgu listesi. Bulgular
  **öneme göre sıralı** (kritik üstte); her bulgu deterministik tetik + (varsa) LLM ajans-dili
  metni. Rapor metni ve erişim taslağı geldikçe (BE-16) göster.
- **Outreach draft kopyalama:** erişim mesajı taslağı **kopyalanabilir**; "gönder" eylemi
  **YOK** (CLAUDE.md: sistem otomatik mesaj göndermez, karar insanda). Kopyala düğmesi + "taslak"
  etiketi net.
- **DESIGN.md:** rapor görünümü, bulgu önem hiyerarşisi, boş/yükleniyor/hata durumları.

**Yapmayacakların:**
- `openapi.yaml` düzenleme; elle tip yazma (gen:api). Sorun → `## Bloke`.
- Mesaj **gönderen** hiçbir UI (yalnız taslak + kopyala). Otomatik gönderim yasak.
- Erişim/gösterim/kaydetme/demografi gösterme (kural 7). Görünürlük skoru bunlardan türetilmez.
- Sabit URL, token dışı `#hex`, sonsuz poll.

**Kabul kriterleri:**
- `gen:api` + `npm run build` + `npx tsc --noEmit` + `npx next lint` sıfır hata.
- Nitelikli hesapta denetim tetiklenip poll ediliyor; nitelikli olmayanda düğme aktif değil.
- Bulgular öneme göre sıralı; deterministik tetik ile LLM metni ayrı görünüyor (BE-13 şema
  ayrımı). Rapor metni/taslak alanları sözleşmedeki alanlara bağlı.
- Erişim taslağı kopyalanabiliyor; "gönder" eylemi hiçbir yerde yok.
- **BE-16 canlı değilken:** UI + tip + poll hazır; canlı uçtan-uca (gerçek rapor metni + taslak)
  BE-16 ayağa kalkınca doğrulanır → o zamana dek `## Devam eden`'de bırak.
- `git grep -nE "#[0-9a-fA-F]{6}" -- web/app web/components` boş; yasak-metrik grep boş;
  `git grep -niE "gönder|send" -- web/` yalnız "taslak/kopyala" bağlamında, mesaj gönderen kod yok.

**Kapanış:** Canlı doğrulama tamamsa `## Biten`'e, değilse `## Devam eden`'e ("canlı BE-16
bekliyor"). `docs/DESIGN.md` güncelle. `git add web/ docs/DESIGN.md docs/TASKS.md`, `fe:`
prefix'iyle commit'le.
