# [GÜVENLİK & TEST] Faz 4 · SEC-9 — denetim + LLM bağımsız denetimi

**BEKLET: BE-16 bitene kadar gönderme.** Bulgu motoru (BE-14), Haiku (BE-15) ve Sonnet (BE-16)
`## Biten`'de olmalı — SEC-9 tüm Faz 4 backend'ini birlikte denetler.

---

Sen Radar projesinin **güvenlik & test** ajanısın. `CLAUDE.md`'yi oku (kural 6, 7, maliyet
disiplini, hukuki sınırlar). Sadece `tests/**`, `.github/**`, `docs/REVIEW.md` ve lint
konfig'lerine yazarsın. `api/**`'ye dokunmazsın — bulgu `## Bloke`'ya.

## GÖREV SEC-9 — Faz 4'ü bağımsız doğrula

**Oku:** `docs/SPEC.md` §5/§6, `docs/TASKS.md` `## Biten` → BE-14/15/16 (ne iddia ettiler),
"Faz 4 karara bağlananlar" (dışarıda kalan 2 kural), "LLM disiplini". `tests/fixtures/README.md`.
`api/` içindeki bulgu motoru, LLM sarmalayıcı, maliyet yardımcısı, audit/outreach persist'i **oku**.

**Dokunabileceğin dosyalar:** `tests/**`, `.github/**`, `docs/REVIEW.md`

**Yapılacaklar (her biri kalıcı test):**

### 1. Deterministik bulgu kuralları
- 5 kuralın her biri eşiğinde tetikleniyor/tetiklenmiyor (SPEC §5 eşikleri): Reels<%10, Bio
  link+tel+CTA yokluğu, sessizlik>14g, CTA'lı oran<%20, hashtag>%70. Sınır değerleri (off-by-one).
- **Dışarıda kalan 2 kural üretilmiyor:** "yorum yanıtsız" ve "görsel tutarsızlık" hiçbir
  hesapta `Finding` üretmiyor (kural 7 kararı). Regresyon testi — biri geri sızarsa kırmızı.
- Görünürlük skoru deterministik: aynı hesap→aynı skor; hiç bulgu→100.

### 2. LLM mock disiplini (kural 6 — kritik)
- **Hiçbir test canlı Anthropic çağrısı yapmıyor.** Haiku ve Sonnet istemcileri mock'lanıyor,
  fixture yanıtlarıyla. Ağ muhafızı altında (SEC-1) tüm Faz 4 testleri yeşil — bunu kanıtla.
- Haiku **tek çağrıda ≤30 gönderi** (çağrı sayacı=1 for N≤30); gönderi başına çağrı yapılmıyor.
- Sonnet **bulgu icat etmiyor:** fixture'da olmayan bir kural çıktıya enjekte edilince
  şema/doğrulama reddediyor (karşı-kanıt kapanış notunda).

### 3. Maliyet denetimi (maliyet disiplini)
- Maliyet yardımcısı `usage`'dan doğru USD üretiyor: cache_read 0.1×, cache_creation 1.25×,
  input 1×, output tam — bilinen bir fixture usage için beklenen USD (sen elle hesapla, magic
  number değil türet). Sonnet tanıtım fiyatı penceresinin doğru oran seçtiğini test et.
- **`audits.llm_cost_usd` boş/NULL kalamıyor:** LLM çağrılan bir denetimden sonra alan > 0 ve
  Haiku+Sonnet toplamına eşit. NOT NULL kısıtı (BE-2) DB seviyesinde de zorlanıyor — test et.

### 4. Gizlilik + hukuki sınır denetimi — `docs/REVIEW.md`
- **Yasak metrik zinciri (kural 7):** LLM promptları/çıktıları ve `audits`/`outreach`
  kayıtlarında `impressions`/`reach`/`saves`/`profile_visits`/demografi **yok**. Rapor metni
  bu metriklerden türetilmiyor.
- **Otomatik mesaj yok (hukuki sınır):** `outreach` kaydı `draft` doğuyor; `api/` içinde mesaj
  **gönderen** hiçbir kod yolu yok (SMTP/HTTP-post-to-DM/vb.). `git grep` ile kanıtla, bulguyu
  `REVIEW.md`'ye PASS/kanıt olarak yaz.
- **Prompt/sır denetimi:** sistem promptları `api/llm/prompts/` versiyonlu dosyalarda, koda
  gömülü değil; `.env.example` yeni anahtarlar değersiz; gerçek anahtar sızıntısı yok.
- **Prompt caching iddiası:** BE-15/16 cache_control kullandığını `usage.cache_read_input_tokens`
  ile gösterdiğini doğrula (fixture usage üzerinden; testte gerçek cache yok ama kod yolu
  cache_control gönderiyor mu — statik kontrol ye터).

**Kabul kriterleri:**
- Yukarıdaki 4 blok testleri `tests/`'te; `pytest` yeşil, **ağ kapalıyken de yeşil** (kural 6
  kanıtı). Maliyet ve bulgu-dışlama testleri karşı-kanıtla ölçülü (kapanış notunda).
- `docs/REVIEW.md`: yasak-metrik zinciri, otomatik-mesaj-yok, prompt/sır maddeleri PASS/kanıtla.
- Yeni bulgu varsa `## Bloke`'ya sahibiyle.

**Kapanış:** `docs/TASKS.md`'de SEC-9'u `## Biten`'e taşı. `git add tests/ .github/
docs/REVIEW.md docs/TASKS.md`, `sec:` commit. Sonra "SEC-9 bitti, Faz 4 bağımsız doğrulandı" de.
