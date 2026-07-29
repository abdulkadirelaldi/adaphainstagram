# [FRONTEND] Faz 6 · FE-8 — kohort ucu bağlama + maliyet alarmı + panel smoke e2e

Sen Radar projesinin **frontend** ajanısın. `CLAUDE.md`'yi oku. Sadece `web/**` ve
`docs/DESIGN.md` altına yazarsın.

## GÖREV FE-8

**Amaç:** Kohort rayını gerçek kohort ucuna bağlamak (FE-3-B1'i kapatmak), maliyet alarmını
üst şeritte göstermek, ve bir panel-tıklama smoke e2e eklemek (SEC-11-N1).

**Oku:** `docs/openapi.yaml` (BE-21: kohort ucu `GET /stats/categories`, `Stats` alarm alanı).
`docs/TASKS.md` `## Bloke` → FE-3-B1 (kendi eski notun: panel `/businesses?limit=200` türetiyor,
200+ hesapta eksik). `## Biten` → BE-23 (kohort ucu davranışı). Kendi DESIGN.md/kohort rayın.

**Dokunabileceğin dosyalar:** `web/**`, `docs/DESIGN.md`

**Yapılacaklar:**
- **Tip yenileme:** `npm run gen:api`.
- **Kohort rayı (FE-3-B1 kapat):** kohort rayını artık `GET /stats/categories`'ten besle;
  `/businesses?limit=200` türetimini **sök**. Kohort<5 kategori işaretini backend'ten al
  (SPEC §4 — o kategoride skor rayı yerine "—" + status, FE-2 deseni korunur).
- **Maliyet alarmı:** üst şeritte `Stats` alarm alanı `true` ise görünür uyarı (renk tek
  taşıyıcı değil — ikon/metin de). Aylık maliyet zaten üst şeritte (`monthly_cost_usd`).
- **Panel smoke e2e (SEC-11-N1):** `web/` içinde küçük bir Playwright smoke: backend fixture
  modunda ayaktayken panel açılıyor, keşif tetikleniyor, tablo dolıyor, bir denetim açılıyor —
  tarayıcı-tıklama akışının kırılmadığını doğrular. Büyük tutma; kritik akışın smoke'u yeter.

**Yapmayacakların:**
- Elle API tipi (gen:api); `openapi.yaml` düzenleme; mesaj gönderen UI (hukuki sınır); yasak
  metrik; sabit URL; token dışı `#hex`.

**Kabul kriterleri:**
- `gen:api` + `npm run build` + `tsc --noEmit` + `next lint` sıfır hata.
- Kohort rayı `/stats/categories`'ten geliyor; `git grep -n "limit=200\|limit: 200" -- web/`
  kohort türetimi için **kalmadı** (sökülü). Kohort<5 işareti gerçek veriyle doğru.
- Maliyet alarmı: alarm `true` fixture'ında üst şeritte görünüyor, `false`'ta yok.
- Panel smoke e2e fixture-mode backend'e karşı yeşil (canlı çağrı yok).
- `#hex` boş; yasak-metrik + gönder/send grep temiz.

**Kapanış:** `docs/TASKS.md`'de FE-8'i `## Biten`'e taşı; `## Bloke` FE-3-B1'e `→ FE-8 ile
kapandı` ekle (BE-23 + FE-8 birlikte). `docs/DESIGN.md` güncelle. `git add web/ docs/DESIGN.md
docs/TASKS.md`, `fe:` commit.
