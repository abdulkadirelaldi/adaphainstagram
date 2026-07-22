# [BACKEND] Faz 2 · BE-6 — adaptör protokolü + sözleşme

Sen Radar projesinin **backend** ajanısın. `CLAUDE.md`'yi oku. Sadece `api/**` ve
`docs/openapi.yaml` altına yazarsın. Bu görev Faz 2'nin ilk iki çıkış kutusunu kapatıyor ve
diğer tüm Faz 2 görevlerini bloke ediyor — sözleşme önce gelir (`CLAUDE.md` kural 3).

## GÖREV BE-6 — `SourceAdapter` protokolü, normalize şema, iki yeni uç

**Amaç:** Üç veri kaynağının arkasına tek bir adaptör soyutlaması koymak ve keşif akışının iki
yeni ucunu sözleşmeye yazmak. **Bu turda gerçek adaptör uygulaması yok** — protokol, şema ve
sözleşme. Uygulamalar BE-7/BE-8'de gelecek.

**Oku:** `docs/SPEC.md` §2 (veri kaynakları tablosu, adaptör deseni, "yeni kaynak tek dosya"),
§1 (akış — keşif nerede duruyor), §3 (`businesses`/`snapshots`/`posts` tabloları — normalize
şema bu tablolara yazılacak, alanlar örtüşmeli), §7 (`POST /discovery/run` → `job_id`,
`GET /jobs/{id}` → kuyruk durumu). BE-2'nin yazdığı modelleri (`api/` içindeki tablolar) da oku.

**Dokunabileceğin dosyalar:** `api/**`, `docs/openapi.yaml`

**Yapılacaklar:**

### 1. `SourceAdapter` protokolü
- `typing.Protocol` ile bir arayüz: bir işletme/handle girdisi alır, **tek normalize çıktı
  şeması** döndürür. Üç kaynağın (Places, IG Business Discovery, Apify) hepsi aynı imzayı
  uygular.
- Normalize çıktı **Pydantic v2 modeli** olsun; alanları `snapshots` ve `posts` tablolarının
  alanlarına düşürülebilir olmalı (SPEC §3). Kaynağa özel ham veri `raw` alanında saklanır
  (SPEC §3 `snapshots.raw`).
- Places farklı bir düzlemde: o **işletme keşfi** yapar (`businesses` kaydı), IG/Apify ise
  var olan işletmeye **snapshot** ekler. İkisini tek protokole zorlama — SPEC §2'yi oku ve
  doğru soyutlamayı seç; iki ayrı protokol (`DiscoverySource` + `ProfileSource`) gerekiyorsa
  öyle yap ve kapanış notunda gerekçelendir.
- "Yeni kaynak eklemek tek dosya olmalı" (SPEC §2): adaptörler bir kayıt/registry üzerinden
  bulunsun, `if source == "apify"` gibi dağınık dallanma olmasın.

### 2. Normalize şema — yasak alan muhafızı
- Çıktı şemasında **erişim/gösterim/kaydetme/profil ziyareti/demografi alanı yok**
  (`CLAUDE.md` kural 7). `posts` yalnızca `like_count`/`comment_count`/`view_count` taşır.
- Apify daha fazla alan döndürebilir; normalize katmanı bu fazlalığı **düşürür**, `raw`'a
  gömer ama normalize şemaya taşımaz.

### 3. Sözleşme — iki yeni uç (`docs/openapi.yaml`)
- `POST /discovery/run` → gövde: keşif parametreleri (en azından bölge/sorgu; SPEC §1 Samsun
  işletmeleri). Yanıt: `{job_id}`. Senkron scraping yok — iş kuyruğa gider, uç anında döner.
- `GET /jobs/{id}` → kuyruk durumu: `job_id`, `status` (`queued|running|done|error` gibi bir
  küme — sen tanımla, açıkça enum'la), ilerleme/sonuç özeti, hata mesajı (nullable).
- Her iki uç da adlandırılmış `components/schemas` şemalarına işaret etsin (inline yok —
  frontend tip üretimi buna bağlı, FE-4 kullanacak).
- Yeni şemalar Faz 1 şemalarıyla çelişmesin; `redocly lint` temiz kalsın.

**Yapmayacakların:**
- Gerçek HTTP çağrısı yapan adaptör gövdesi yazma (BE-7/BE-8). Protokol + normalize şema +
  belki `NotImplementedError` iskeletleri yeterli.
- arq worker / cache / job yürütücü yazma (BE-9).
- Yasak metrik alanı ekleme.

**Kabul kriterleri:**
- `redocly lint docs/openapi.yaml` hatasız; `POST /discovery/run` ve `GET /jobs/{id}` tanımlı,
  gövdeleri adlandırılmış şema.
- Normalize Pydantic modeli import edilip örneklenebiliyor; `mypy api/` protokol uyumunu
  doğruluyor (bir adaptör iskeleti protokolü uygulamıyorsa mypy patlıyor — bunu bir örnekle
  göster).
- `git grep -nE "impressions|reach|saves|profile_views|demographics|follower_age|gender" -- api/`
  boş.
- Adaptör kaydı çalışıyor: kayıtlı kaynak adından adaptör örneği alınabiliyor, bilinmeyen ad
  net bir hata veriyor. (Küçük bir doğrulama scripti/testiyle göster; testi `api/` içine değil,
  güvenlik ajanı `tests/`'e yazacak — sen elle doğrula, kapanış notuna yaz.)
- `ruff check .` + `ruff format --check` + `mypy api/` + `pytest` yeşil (CI pin'leri: ruff
  0.12.0, mypy 2.3.0).

**Kapanış:** `docs/TASKS.md`'de BE-6'yı `## Biten` altına tek satır sonuç notuyla taşı
(tek protokol mü iki protokol mü seçtiğini ve neden). Faz 2 çıkış kutusu #1 ve #2'yi
işaretle. `git add api/ docs/openapi.yaml docs/TASKS.md`, `be:` prefix'iyle commit'le. Sonra
orkestra şefine "BE-6 dondu; BE-7, BE-8, SEC-4, FE-4 sözleşmeye başlayabilir" de.
