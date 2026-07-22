# Fixture'lar — dış-API ham yanıt örnekleri

Bu dizindeki JSON'lar üç kaynağın **ham** (normalize edilmemiş) çıktısının sabit,
sahte, tekrarlanabilir örnekleridir (`CLAUDE.md` kural 6). Hiçbiri gerçek işletme/kişi
verisi taşımaz — uydurma ama gerçekçi Samsun örnekleridir.

**Ham ≠ normalize.** Adaptör (BE-7/BE-8) bu ham biçimi okur ve `api/adapters/base.py`
içindeki `Normalized*` şemalarına çevirir. Fixture'ın kendisi normalize şema değildir;
adaptörün **girdisidir**. Eşleme aşağıda.

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

**Eksik-alan yolu:** `Sahil Kahve Evi` (`ChIJradar0000kafe0003`) telefonsuz **ve** websitesiz —
`phone`/`website` `None` olmalı. `Karadeniz Oto Galeri` websitesiz ama telefonlu. Normalize'ın
`None` yolunu bu iki kayıt test eder.

## `ig_business_discovery.json` → `NormalizedProfile` (+ `NormalizedPost[]`)

IG Graph API Business Discovery yanıtı. Kök `business_discovery` nesnesi, gönderiler
`business_discovery.media.data[]` altında. **Temiz kaynak:** yasak alan içermez.

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

Apify Instagram Scraper çıktısı. Düz nesne, gönderiler `latestPosts[]` altında.
**Business Discovery çalışmazsa yedek** (SPEC §2). Apify çok daha fazla alan döndürür.

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
