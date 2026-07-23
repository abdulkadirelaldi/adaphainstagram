# [GÜVENLİK & TEST] Faz 2 · SEC-6 — fixture'ı 20 işletmeye genişlet + handle eşleme

Sen Radar projesinin **güvenlik & test** ajanısın. `CLAUDE.md`'yi oku. Sadece `tests/**`,
`.github/**`, `docs/REVIEW.md` ve lint konfig dosyalarına yazarsın.

**Bu görev BE-9'u bloke ediyor** — "tek komutla 20 işletme" demo'su senin genişlettiğin
fixture'la çalışacak. Önce bu.

## GÖREV SEC-6 — keşif demo fixture seti

**Amaç:** Places fixture'ını Faz 2 bitiş kriterini (SPEC §8: "tek komutla 20 işletme
keşfedilip snapshot'ı alınıyor") besleyecek büyüklüğe çıkarmak ve IG handle eşleme
sözleşmesine göre bağlantılar yerleştirmek.

**Oku:**
- `docs/TASKS.md` → "**IG handle eşleme sözleşmesi (Faz 2)**" — bu sözleşme fixture'ının
  şeklini belirliyor, harfiyen uy.
- `docs/SPEC.md` §1 (keşif→handle eşleme→triyaj akışı), §2 (kaynaklar).
- Kendi SEC-4 fixture'ların (`tests/fixtures/places_response.json` vb.) ve
  `tests/fixtures/README.md`.

**Dokunabileceğin dosyalar:** `tests/**`, `docs/REVIEW.md`

**Yapılacaklar:**
- `places_response.json`'ı **~20 uydurma ama gerçekçi Samsun işletmesine** genişlet
  (SPEC §1: klinik, kuyumcu, oto galeri, emlak, kafe, kuaför… kategori çeşitliliği olsun ki
  Faz 3 kohort medyanı test edilebilsin — SPEC §4 kohort<5 kuralı).
- **Handle eşleme sözleşmesine göre bağlantılar:**
  - İşletmelerin bir kısmı (~14) `raw` içinde website/sosyal alanda `instagram.com/{handle}`
    biçiminde açık bir bağlantı taşısın → BE-9 bunlardan handle çıkaracak, snapshot alacak.
  - Bir kısmı (~6) hiç instagram bağlantısı taşımasın → `ig_handle=NULL` yolu, snapshot yok.
  - Sözleşme gereği **ad benzerliğinden tahmin edilmeyecek** — o yüzden handle'sız işletmelerde
    ada benzeyen ama instagram olmayan link koymak testi güçlendirir (yanlış-pozitif tuzağı).
- **Profil fixture'larını handle'larla eşle:** handle taşıyan her işletme için BE-9'un profil
  çekiminde kullanacağı bir yanıt olmalı. Tek tek 14 ayrı dosya şart değil — `apify_profile.json`
  ve `ig_business_discovery.json`'ı handle→profil eşlemesi olacak biçimde yapılandır (ör. handle
  anahtarlı bir sözlük ya da adaptörün handle'a göre seçebileceği bir liste). Hangi yapıyı
  seçtiğini `README.md`'ye yaz — BE-9 buna bakacak.
- **Fallback yolu için veri:** en az bir handle Business Discovery'de boş/eksik dönsün ki BE-9
  Apify fallback'ini (BE-8'in servisi) demo'da gerçekten tetikleyebilsin.
- **Cache yolu için veri:** en az iki işletme **aynı** handle'a işaret etsin ya da README'de
  "şu handle 7 gün cache testinde tekrar kullanılacak" diye işaretle — SEC-5 cache denetimi
  buna dayanacak.
- `README.md`'yi güncelle: 20 işletmenin kaçı handle'lı, handle→profil eşleme yapısı, fallback
  ve cache için işaretli handle'lar.

**Yapmayacakların:**
- `api/`'ye dokunma. BE-9 çıkarım mantığını sen yazmazsın; sadece sözleşmeye uygun veri
  sağlarsın.
- Gerçek işletme/kişi verisi koyma (kural 6 ruhu — sabit, sahte, tekrarlanabilir).
- Fixture'a yasak metrik alanı taşımayı unutma: `apify_profile.json` yasak alanları (SEC-4'te
  koydun) **korusun** — genişletirken silme, BE-9'un düşürmesini SEC-5 doğrulayacak.

**Kabul kriterleri:**
- `places_response.json` ~20 işletme, kategori çeşitliliği var, hepsi geçerli JSON.
- Handle çıkarımı test edilebilir: en az bir işletme açık instagram URL taşıyor, en az biri
  taşımıyor, en az biri instagram'a benzeyen ama instagram olmayan tuzak link taşıyor.
- Handle→profil eşleme yapısı README'de belgeli ve fixture'da tutarlı.
- Fallback ve cache için işaretli handle'lar mevcut.
- `pytest` yeşil (mevcut kontrat testleri genişletilmiş fixture'la hâlâ geçiyor); ağ kapalıyken
  de yeşil.
- `ruff` + `mypy` (test hedefliyse) temiz.

**Kapanış:** `docs/TASKS.md`'de SEC-6'yı `## Biten`'e taşı ve backend'e "fixture 20 işletmeye
genişledi, handle→profil eşlemesi README'de, BE-9 başlayabilir" satırını not düş.
`git add tests/ docs/REVIEW.md docs/TASKS.md` (`git add -A` yasak), `sec:` prefix'iyle commit'le.
