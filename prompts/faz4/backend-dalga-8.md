# [BACKEND] Faz 4 · Dalga 8 — BE-15 (Haiku sınıflandırma) + BE-16 (Sonnet sentez)

Sen Radar projesinin **backend** ajanısın. `CLAUDE.md`'yi oku (maliyet disiplini + kural 6/7).
Sadece `api/**`, `.env.example`, `pyproject.toml` altına yazarsın. İki görev, sırayla, ayrı
commit'ler. Bu iki görev Faz 4'ün kalan üç çıkış kutusunu kapatıyor.

**Ortak kurallar (`docs/TASKS.md` → "LLM disiplini" ve "Faz 4 karara bağlananlar"):**
- Anthropic SDK. Model id'leri: sınıflandırma **`claude-haiku-4-5`**, sentez **`claude-sonnet-5`**.
  Başka model kullanma; tarih son eki ekleme.
- Promptlar `api/llm/prompts/` altında **versiyonlu dosyalar** (SPEC §6), koda gömülmez.
- **Testte canlı Anthropic çağrısı YOK** (kural 6). LLM istemcisi enjekte edilebilir olsun;
  test sahte istemci + fixture yanıtla çalışır. `git grep` ile gerçek anahtar sızıntısı olmaz.
- Anahtar `.env`'den (`pydantic-settings`); `.env.example`'a **değersiz** ekle.

**Maliyet hesabı (ikisinde de aynı yardımcı):** `response.usage`'dan USD üret:
```
cost = (input_tokens               * in_rate
      + cache_creation_input_tokens * in_rate * 1.25
      + cache_read_input_tokens     * in_rate * 0.10
      + output_tokens              * out_rate) / 1_000_000
```
Oranlar (per 1M token) bir sabit tabloda, **kaynak + tarih yorumuyla**:
- Haiku 4.5: input **$1.00**, output **$5.00**
- Sonnet 5: input **$3.00**, output **$15.00** — **tanıtım fiyatı $2.00/$10.00, 2026-08-31'e
  kadar** (bugün tanıtım penceresi içinde). Oranı pencereye göre seçen bir tablo yap, hangi
  oranı kullandığını `audits`'e yazdığın kayıtta izlenebilir bırak.
`Numeric`/`Decimal` kullan, `float` ile para yuvarlama yapma.

---

## GÖREV BE-15 — Haiku 4.5 batch sınıflandırma

**Amaç:** Bir hesabın gönderilerini tek çağrıda sınıflandırmak (içerik sütunu, ton etiketi,
görsel kalite notu, CTA tespiti), katı JSON çıktı, Pydantic doğrulamalı.

**Oku:** `docs/SPEC.md` §6 (Haiku katmanı — tek çağrıda 30 gönderi, katı JSON şema). BE-14'ün
bulgu motoru ve `audits` persist'i (Haiku çıktısı denetime girdi olacak).

**Dokunabileceğin dosyalar:** `api/**`, `api/llm/prompts/`, `.env.example`, `pyproject.toml`

**Yapılacaklar:**
- `api/llm/` altında Anthropic istemci sarmalayıcı; istemci **enjekte edilebilir** (test sahte
  verir).
- Haiku sınıflandırma: **tek `messages.create` çağrısında ≤30 gönderi** — gönderi başına ayrı
  çağrı **yasak** (CLAUDE.md). 30'dan fazla gönderi varsa 30'luk gruplara böl, her grup bir çağrı.
- Çıktı **katı JSON**, Pydantic v2 ile doğrulanır (`messages.parse` + Pydantic model, ya da
  `output_config.format` json_schema). Şema: gönderi başına içerik sütunu + ton + görsel not +
  CTA (bool). Şemaya uymayan yanıt reddedilir/retry.
- **Prompt caching:** sistem promptu + sabit sınıflandırma yönergesi/benchmark `cache_control`
  ile cache'lenir (prefix-match — sabit içerik önce, gönderiler sonra). Sonuç `usage`'da
  `cache_read_input_tokens` ile doğrulanır. Haiku minimum cacheable prefix ~4096 token — sistem
  promptu bunun altındaysa cache tetiklenmez; prompt dosyasında bunu hesaba kat.
- **Maliyet:** her çağrının maliyetini yukarıdaki yardımcıyla hesapla, sınıflandırma toplam
  maliyetini döndür (BE-16 Sonnet maliyetiyle toplanıp `audits.llm_cost_usd`'ye yazılacak).

**Kabul kriterleri:**
- Sahte istemci + fixture Haiku yanıtıyla: N gönderi (N≤30) **tek çağrıda** sınıflandırılıyor
  (çağrı sayacı=1); N>30 için grup sayısı `ceil(N/30)`.
- Çıktı Pydantic'e doğruluyor; bozuk JSON reddediliyor (test et).
- `usage`'dan maliyet doğru hesaplanıyor: cache_read 0.1×, cache_creation 1.25× dahil bir
  fixture usage ile beklenen USD elle doğrulandı (kapanış notuna yaz).
- Yasak metrik (kural 7) çıktı şemasında yok; prompt bunları istemiyor.
- `ruff` + `mypy api/` + `pytest` yeşil; `git grep -nE "sk-ant|ANTHROPIC_API_KEY.*=.*['\"]"
  -- ':!*.example'` boş.

**Kapanış:** `docs/TASKS.md`'de BE-15'i `## Biten`'e taşı. Faz 4 kutusu #2'yi işaretle.
`git add api/ .env.example pyproject.toml docs/TASKS.md`, `be:` commit. Sonra BE-16'ya geç.

---

## GÖREV BE-16 — Sonnet 5 sentez + outreach draft + maliyet kaydı

**Amaç:** Metrikler + BE-14 bulguları + Haiku sınıflandırması + kohort istatistiğinden rapor
metni ve erişim mesajı taslağı üretmek; `outreach` kaydını `draft` doğurmak; `audits.llm_cost_usd`'ye
**gerçek toplam** maliyeti yazmak.

**Oku:** `docs/SPEC.md` §6 (Sonnet katmanı — girdi/çıktı, sistem promptu cache'lenir), §5
(bulguları ajans diline çevirme — LLM icat etmez), §3 (`audits`, `outreach`). BE-14 (`Finding`
LLM-metni alanı boş bıraktı — burada doldur), BE-15 (Haiku çıktısı + maliyet).

**Dokunabileceğin dosyalar:** `api/**`, `api/llm/prompts/`, `.env.example`

**Yapılacaklar:**
- Sonnet 5 tek sentez çağrısı: girdi = deterministik bulgular (BE-14) + metrikler + Haiku
  sınıflandırması (BE-15) + kohort istatistikleri. Çıktı = rapor metni + `outreach` draft metni.
- **LLM bulgu icat etmez** (SPEC §5): Sonnet yalnız var olan `Finding`'leri ajans diline
  çevirir ve önceliklendirir; yeni kural/bulgu üretmez. Prompt bunu açıkça sınırlasın; çıktı
  şeması bulgu **eklemeyi** yapısal olarak engellesin (var olan bulgu id'lerine metin bağla).
- **Prompt caching:** sistem promptu + benchmark tablosu `cache_control` ile sabitlenir (SPEC §6);
  oynak girdi (bu hesabın metrikleri/bulguları) breakpoint'ten sonra. `cache_read_input_tokens`
  ile doğrula.
- **`outreach` kaydı `draft` doğar** (CLAUDE.md hukuki sınır — sistem otomatik mesaj göndermez).
  `status` varsayılanı zaten `draft` (BE-2); burada da `draft` dışında bir değer yazma. Gönderme
  eylemi **yok**.
- **Maliyet kaydı:** Sonnet maliyeti + BE-15 Haiku maliyeti = bu denetimin gerçek toplamı;
  `audits.llm_cost_usd`'ye yaz (BE-14'ün 0'ını güncelle). Alan **boş/0 kalamaz** eğer LLM
  çağrıldıysa (maliyet disiplini). Denetim akışı: BE-14 deterministik → BE-15 Haiku → BE-16
  Sonnet → tek `audits` kaydı gerçek maliyetle.
- Bu üç fazı `POST /businesses/{id}/audit` job'una bağla (BE-14 job'una Haiku+Sonnet fazlarını
  ekle). Fixture modunda (BE-10) LLM istemcisi de sahte/fixture olsun — canlı Anthropic çağrısı
  yok.

**Kabul kriterleri:**
- Sahte Sonnet istemci + fixture yanıtla: `GET /audits/{id}` bulgu listesi + görünürlük skoru +
  **rapor metni** döndürüyor; her `Finding`'in LLM ajans-dili metni dolu, deterministik tetik
  hâlâ ayrı. **Faz 4 çıkış kutusu #1'in "bir hesap için rapor metni üretiliyor" hedefi** karşılandı.
- `outreach` kaydı oluştu ve `status='draft'`; gönderen kod yok (`git grep -niE "send|gönder"
  -- api/` yalnız yorum/ad bağlamında, mesaj gönderen çağrı yok).
- `audits.llm_cost_usd` **> 0** ve Haiku+Sonnet toplamına eşit (fixture usage'larla elle
  doğrulandı, kapanış notuna yaz). LLM çağrılmayan bir denetim yolu varsa 0 kalması meşru —
  ama LLM çağrıldıysa 0 kalamaz.
- Sonnet çıktısı bulgu **eklemiyor**: fixture'a olmayan bir kural enjekte etmeyi dene → şema/
  doğrulama reddediyor (kural: LLM icat etmez).
- Fixture modunda `POST /businesses/{id}/audit` → job → `GET /audits/{id}` uçtan uca çalışıyor,
  canlı Anthropic çağrısı yok.
- `ruff` + `mypy api/` + `pytest` yeşil; yasak-metrik + anahtar-sızıntı grep boş.

**Kapanış:** `docs/TASKS.md`'de BE-16'yı `## Biten`'e taşı. Faz 4 kutusu #3 ve #4'ü işaretle
(#1 rapor metni kısmı da tamam). `git add api/ .env.example docs/TASKS.md`, `be:` commit. Sonra
orkestra şefine "BE-15+BE-16 bitti, Faz 4 dört kutu hazır; SEC-9 bağımsız denetim yapabilir,
FE-6 canlı doğrulanabilir" de.
