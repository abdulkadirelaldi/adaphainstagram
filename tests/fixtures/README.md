# Fixture'lar — dış-API ham yanıt örnekleri

Bu dizindeki JSON'lar üç kaynağın **ham** (normalize edilmemiş) çıktısının sabit,
sahte, tekrarlanabilir örnekleridir (`CLAUDE.md` kural 6). Hiçbiri gerçek işletme/kişi
verisi taşımaz — uydurma ama gerçekçi Samsun örnekleridir.

**Ham ≠ normalize.** Adaptör (BE-7/BE-8) bu ham biçimi okur ve `api/adapters/base.py`
içindeki `Normalized*` şemalarına çevirir. Fixture'ın kendisi normalize şema değildir;
adaptörün **girdisidir**. Eşleme aşağıda.

---

## SEC-8 — skorlama demo seti (100 hesap, skor sinyalleri çeşitli)

Faz 3 bitiş kriteri "100 hesap taranıp panelde skorlarıyla listeleniyor" (SPEC §8) bu set
üzerinden çalışır. Fixture 20→**100 işletme**ye büyüdü: **SEC-6'nın ilk 20 hesabı aynen
korundu** (adaptör/cache/fallback testlerinin dayandığı bilinen değerler), üzerine 80 yeni
hesap eklendi. Yeni hesaplar deterministik üretildi (indeks tabanlı, rastgelelik yok).

### Referans zaman — SÖZLEŞME (BE-11 için)

Tüm `posted_at`/`timestamp` değerleri **sabit ISO** tarihlerdir; göreli "bugün" **yoktur**
(testler `currentDate`'e bağlı olmamalı). Skorlama motoru (BE-11) 90 gün aktiflik penceresini
şu sabit referansa göre kurar:

> **`REFERENCE_NOW = 2026-07-15T00:00:00+00:00`** → 90 gün penceresi: 2026-04-16 … 2026-07-15.

Yeni hesapların gönderileri bu referanstan geriye sabit gün ofsetleriyle yerleştirildi.

### 100 işletme, kategori dağılımı (kohort için)

SPEC §4 kohort<5 kuralı test edilebilsin diye **hem ≥5 hem <5** kategori var. Dokuz kategori
≥5 (kohort medyanı hesaplanır), üçü <5 (potansiyel hesaplanmaz → `watch`):

| Kategori | Adet | Kohort | Kapasite (SPEC §4) |
|---|---|---|---|
| `cafe` | 15 | ≥5 | orta |
| `hair_salon` | 15 | ≥5 | orta |
| `real_estate_agency` | 11 | ≥5 | yüksek |
| `jewelry_store` | 10 | ≥5 | yüksek |
| `dental_clinic` | 10 | ≥5 | yüksek |
| `car_dealer` | 9 | ≥5 | yüksek |
| `restaurant` | 8 | ≥5 | orta |
| `beauty_salon` | 8 | ≥5 | orta |
| `gym` | 6 | ≥5 | orta |
| `florist` | 3 | **<5 → watch** | düşük |
| `gift_shop` | 3 | **<5 → watch** | düşük |
| `pet_store` | 2 | **<5 → watch** | düşük |

**Handle:** 83 işletme instagram URL'li (`raw.websiteUri` → snapshot yolu), **17 handle'sız**
(`ig_handle=NULL`, taranmaz). SEC-6'nın 4 yanlış-pozitif tuzağı korundu; yeni NULL'lar da
facebook/düz-site/websitesiz karışımı.

**Profil eşleme:** `ig_business_discovery.json` → 71 dolu BD profili + 12 boş `{}` (fallback);
`apify_profile.json` → 12 fallback profili (SEC-6'nın 2'si + 10 yeni), **hepsi yasak alanları
korur** (kural 7, BE-9 düşürür, SEC-5 doğrular).

### Skor sinyalleri — arketipler (SPEC §4)

Yeni hesaplar skorların tüm bantlara yayılması için arketiplere göre kuruldu:

- **Aktiflik** (`posted_at` yoğunluğu + en uzun sessizlik): `active` (≈2/hafta, kısa sessizlik
  → yüksek), `moderate` (orta), `dormant` (uzun sessizlik → düşük), `dead` (**0 gönderi →
  aktiflik 0 → çarpım çöker → `rejected`**).
- **Potansiyel** (yüksek = kötü yönetim = bizim için iyi): `bad` yönetim = Reels yok (hep
  IMAGE), düşük etkileşim (like/comment kategori medyanı altında), CTA'sız caption →
  **yüksek potansiyel**. `good` yönetim = Reels + yüksek etkileşim + CTA'lı caption → düşük
  potansiyel. `avg` = karışık.
- **Kapasite** (ödeyebilir mi): kategori ağırlığı (yukarıdaki tablo) + `followersCount` +
  `websiteUri` varlığı + `userRatingCount`. Yüksek-kapasite hesaplar yüksek takipçi + yüksek
  rating taşır.

### Skor-bandı hedefleri (tasarım niyeti — kesin skoru BE-11 hesaplar)

Bunlar **yaklaşık** hedeftir; gerçek skor/durum BE-11'in motorundan çıkar. Fixture bu dağılımı
üretecek biçimde kuruldu (SEC-7 skorlama testlerine zemin):

| Bant | ≈ Hesap | Nasıl kuruldu |
|---|---|---|
| `rejected` (<40) | ~18 | `dead` aktiflik (0 gönderi) → çarpım çöker, kategori/kapasite fark etmez |
| `qualified` (≥70) | ~8 | `active` + `bad` yönetim (yüksek potansiyel) + yüksek-kapasite kategori + yüksek takipçi/rating |
| `watch` (40–69) | ~57 | `moderate`/`dormant` + `good`/`avg` yönetim (orta skor) **artı** 8 küçük-kohort hesabı (florist/pet/gift → kohort<5 → potansiyel hesaplanmaz → `watch`) |
| skorlanmaz | 17 | handle'sız (NULL) — keşfedilir ama taranmaz, `triage_scores` satırı doğmaz |

**Kohort<5 kanıtı:** `florist`(3)/`gift_shop`(3)/`pet_store`(2) hesaplarının hepsi handle'lı
(snapshot alınır) ama kohortları 5'in altında → SPEC §4 gereği potansiyel alt skoru
hesaplanmaz, bu hesaplar `watch` olur. SEC-7 bunu motorda doğrular.

---

## SEC-6 — keşif demo seti (ilk 20 hesap, SEC-8'de korundu)

Faz 2 bitiş kriteri "tek komutla 20 işletme keşfedilip snapshot'ı alınıyor" (SPEC §8)
bu 20-hesap çekirdeği üzerinden çalışır (SEC-8'de aynen korundu). Fixture'lar `docs/TASKS.md`
"IG handle eşleme sözleşmesi"ne uyar.

**20 işletme, kategori dağılımı** (SPEC §4 kohort testi için hem ≥5 hem <5 kategori var):

| Kategori | Adet | Kohort |
|---|---|---|
| `cafe` | 5 | ≥5 → medyan hesaplanabilir |
| `hair_salon` | 5 | ≥5 → medyan hesaplanabilir |
| `jewelry_store` | 3 | <5 → `watch` yolu |
| `real_estate_agency` | 3 | <5 → `watch` yolu |
| `dental_clinic` | 2 | <5 → `watch` yolu |
| `car_dealer` | 2 | <5 → `watch` yolu |

**Handle eşleme (14 handle'lı, 6 handle'sız).** Handle YALNIZCA `raw`'daki açık bir
`instagram.com/{handle}` URL'sinden türetilir, ad benzerliğinden **tahmin edilmez**
(sözleşme; yanlış eşleme = yanlış işletmeye rapor = hukuki ihlal).

> **⚠️ Handle'ın taşındığı yer `websiteUri`.** Places (New) alan maskesi
> (`api/adapters/places.py`) ayrı bir sosyal-bağlantı alanı **istemiyor**; ham `place`
> nesnesinde URL taşıyan tek alan `websiteUri`. Bu yüzden handle'lı işletmelerin
> `websiteUri`'si doğrudan instagram URL'sidir. BE-9 çıkarımı `raw` içindeki instagram
> URL'sini tarar. (Bu bir kısıt, bulgu değil — `docs/REVIEW.md` SEC-6'da not edildi.)

Handle taşımayan 6 işletmenin 4'ü **yanlış-pozitif tuzağı** — çıkarım bunlardan handle
üretirse sözleşme kırılır, hepsi `ig_handle=NULL` kalmalı:

| İşletme | `websiteUri` | Neden handle YOK |
|---|---|---|
| Yıldız Kuyumculuk | `https://yildizkuyum.example.com` | instagram değil |
| Atlas Oto Galeri | `https://www.facebook.com/atlasotogaleri` | ad eşleşir ama facebook |
| Sırma Kuaför | `https://help.instagram.com/` | `instagram.com` alt alan adı, profil değil |
| Nostalji Kafe | `https://www.instagramm.example.com/nostaljikafe` | benzer alan adı (`instagramm`) |
| Güneş Diş Kliniği | *(yok)* | `websiteUri` alanı yok |
| Ada Emlak | *(yok)* | `websiteUri` + telefon yok |

**Handle → profil eşleme yapısı.** İki profil fixture'ı artık **handle-anahtarlı**:
kök `"profiles"` sözlüğü, anahtar = handle, değer = o handle için ham yanıt. BE-9'un
enjekte ettiği sahte client `fetch_profile(handle)` çağrısında handle'a göre buradan seçer.

- `ig_business_discovery.json` → `profiles`: **12 handle** dolu BD yanıtı taşır;
  **2 handle** (`sahilkahveevi`, `cadde19kafe`) boş `{}` — BD veri vermedi demektir.
- `apify_profile.json` → `profiles`: **2 handle** (`sahilkahveevi`, `cadde19kafe`) Apify
  profili taşır (fallback hedefi).

**Fallback yolu (SPEC §2).** `sahilkahveevi` ve `cadde19kafe` BD'de boş döner →
profil servisi Apify'a düşer. BE-9 demo'sunda gerçek fallback bu iki handle ile tetiklenir.

**Cache yolu (7 gün, SEC-5).** `atakumdisklinigi` handle'ı SEC-5'in 7-günlük cache
denetiminde **tekrar çekim** senaryosu için kullanılacak: ilk çekim snapshot yazar,
7 gün içindeki ikinci istek cache'ten dönmeli, ikinci snapshot **oluşmamalı**. BE-9
persist'i idempotent, cache'i BE-9 sarıyor.

---

## `places_response.json` → `NormalizedBusiness` → `businesses` tablosu

Google Places API (New) `places:searchText` yanıtı. Kök `places[]` dizisi, her eleman bir işletme.

| Ham alan (Places) | Normalize alan | Not |
|---|---|---|
| `id` | `place_id` | |
| `displayName.text` | `name` | iç içe; `.text` alınır |
| `primaryType` | `category` | `types[]` değil, birincil tip |
| `formattedAddress` | `address` | |
| `nationalPhoneNumber` | `phone` | yoksa `None` |
| `websiteUri` | `website` | yoksa `None` |
| `userRatingCount` | `rating_count` | |
| tüm ham nesne | `raw` | eksiksiz gömülür |
| `rating`, `types`, `internationalPhoneNumber` | — | `raw`'da kalır, yüzeye çıkmaz |

**Eksik-alan yolu (normalize `None`):** `Sahil Kahve Evi` (`ChIJradar00kafe0003`) telefonsuz
(`nationalPhoneNumber` yok → `phone=None`). `Güneş Diş Kliniği` ve `Ada Emlak` websitesiz
(`websiteUri` yok → `website=None`); `Ada Emlak` ayrıca telefonsuz. Bu kayıtlar normalize'ın
`None` yolunu test eder.

## `ig_business_discovery.json` → `NormalizedProfile` (+ `NormalizedPost[]`)

IG Graph API Business Discovery yanıtları. **Handle-anahtarlı:** kök `profiles` sözlüğü,
her değer ham BD yanıtı (`business_discovery` nesnesi, gönderiler
`business_discovery.media.data[]` altında). Boş `{}` = BD veri veremedi → fallback.
**Temiz kaynak:** yasak alan içermez. Aşağıdaki eşleme her `profiles[<handle>]` değeri içindir.

Profil düzeyi:

| Ham alan (IG BD) | Normalize alan | Not |
|---|---|---|
| — (sabit) | `source` | adaptör `"business_discovery"` yazar |
| `followers_count` | `followers` | |
| `follows_count` | `follows` | |
| `media_count` | `media_count` | |
| `biography` | `biography` | |
| `website` | `external_url` | |
| — | `is_professional` | BD yalnız işletme hesabı döndürür; adaptör kararı |
| tüm ham nesne | `raw` | |

Gönderi düzeyi (`media.data[]` → `NormalizedPost`):

| Ham alan | Normalize alan | Not |
|---|---|---|
| `id` | `ig_id` | |
| `media_type` | `media_type` | `IMAGE`/`VIDEO`/`CAROUSEL_ALBUM` |
| `caption` | `caption` | |
| `like_count` | `like_count` | |
| `comments_count` | `comment_count` | ad farkı: `comments_count`→`comment_count` |
| `timestamp` | `posted_at` | ISO 8601 |
| `permalink` | `permalink` | |
| `media_url` / `thumbnail_url` | `thumb_url` | video'da `thumbnail_url` |
| — | `view_count` | BD gönderi izlenmesi vermez → `None` |

## `apify_profile.json` → `NormalizedProfile` (+ `NormalizedPost[]`)

Apify Instagram Scraper çıktıları. **Handle-anahtarlı:** kök `profiles` sözlüğü, her değer
bir profil (gönderiler `latestPosts[]` altında). **Business Discovery çalışmazsa yedek**
(SPEC §2) — bu fixture yalnızca fallback handle'larını (`sahilkahveevi`, `cadde19kafe`)
taşır. Apify çok daha fazla alan döndürür. Aşağıdaki eşleme her `profiles[<handle>]` içindir.

Profil düzeyi:

| Ham alan (Apify) | Normalize alan | Not |
|---|---|---|
| — (sabit) | `source` | adaptör `"apify"` yazar |
| `followersCount` | `followers` | |
| `followsCount` | `follows` | |
| `postsCount` | `media_count` | |
| `biography` | `biography` | |
| `externalUrl` | `external_url` | |
| `isBusinessAccount` | `is_professional` | |
| tüm ham nesne | `raw` | |

Gönderi düzeyi (`latestPosts[]` → `NormalizedPost`):

| Ham alan | Normalize alan | Not |
|---|---|---|
| `id` | `ig_id` | |
| `type` | `media_type` | `Image`/`Video`/`Sidecar` |
| `caption` | `caption` | |
| `likesCount` | `like_count` | |
| `commentsCount` | `comment_count` | |
| `videoViewCount` | `view_count` | yalnız video'da; yoksa `None` |
| `timestamp` | `posted_at` | |
| `url` | `permalink` | |
| `displayUrl` | `thumb_url` | |
| `latestComments[]` | — | `raw`'da kalır; yorum **metni** normalize yüzeye çıkmaz |

### ⚠️ Yasak alanlar — bilerek konuldu (CLAUDE.md kural 7)

Apify gerçekte aşağıdaki metrikleri döndürür. Fixture'a **bilerek** konuldu ki normalize
katmanının onları **düşürdüğü** SEC-5'te ve backend'in kendi doğrulamasında kanıtlanabilsin.
Bu alanlardan **hiçbiri** normalize şemaya, DB'ye, rapora veya arayüze girmez —
`NormalizedProfile`/`NormalizedPost` `extra="forbid"` ile bunları reddeder.

Profil düzeyi: `impressions`, `reach`, `saves`, `profileVisits`, `followerDemographics`
(`ageRanges`, `gender`).
Gönderi düzeyi: `impressions`, `reach`, `saved`.

`tests/test_normalize_contract.py` bu alan adlarını `NormalizedProfile`'a vermeyi dener ve
`ValidationError` bekler — yani "yasak alan normalize yüzeye çıkarsa test kırmızı" bir makine
kuralıdır, tavsiye değil.
