# Radar — şartname

## 1. Akış

```
Google Places  →  işletme kaydı  →  IG handle eşleme  →  triyaj taraması
                                                              ↓
                                              skor < 40  →  elendi (arşiv)
                                              40–69      →  izlemede (90 gün sonra tekrar)
                                              ≥ 70       →  derin denetim
                                                              ↓
                                        rapor PDF + erişim mesajı taslağı  →  insan onayı
```

Triyaj ucuzdur ve LLM kullanmaz. Derin denetim pahalıdır ve sadece nitelikli adaylara çalışır.
Bu ayrım ürünün ekonomisinin tamamıdır; bulanıklaştırma.

## 2. Veri kaynakları

| Kaynak | Ne verir | Ne zaman |
|---|---|---|
| Google Places API | işletme adı, kategori, adres, telefon, site, değerlendirme sayısı | keşif |
| IG Business Discovery | takipçi, takip, medya sayısı, bio, site, son gönderiler | hedef işletme hesabıysa |
| Apify Instagram Scraper | profil + gönderi + yorum | Business Discovery çalışmazsa |

Adaptör deseni zorunlu: `SourceAdapter` protokolü, üç uygulama, tek normalize çıktı şeması.
Yeni kaynak eklemek tek dosya olmalı.

## 3. Veri modeli

```
businesses      id, place_id, name, category, address, phone, website,
                ig_handle, rating_count, discovered_at
snapshots       id, business_id, captured_at, source, followers, follows,
                media_count, biography, external_url, is_professional, raw
posts           id, snapshot_id, ig_id, media_type, caption, like_count,
                comment_count, view_count, posted_at, permalink, thumb_url
triage_scores   id, business_id, snapshot_id, score, activity, potential,
                capacity, status, computed_at
audits          id, business_id, visibility_score, findings, pdf_path,
                llm_cost_usd, generated_at
outreach        id, audit_id, channel, draft, status, sent_at, replied_at
```

`status` alanları: triyaj `qualified | watch | rejected`, erişim
`draft | sent | opened | replied | meeting | won | lost`.

## 4. Triyaj skoru

Üç alt skor, her biri 0–100.

**Aktiflik** — hesap yaşıyor mu.
Son 90 gündeki gönderi sayısı ve en uzun sessizlik. 0 gönderi → 0. Haftada 2+ gönderi ve
14 günden kısa en uzun sessizlik → 100.

**Potansiyel** — kötü mü yönetiliyor. Yüksek olması bizim için iyi.
Dört sinyalin ortalaması: Reels oranı düşüklüğü, etkileşim oranının aynı kategorideki
medyana göre düşüklüğü, caption'larda CTA yokluğu, yorum yanıt oranı düşüklüğü.

**Kapasite** — ödeyebilir mi.
Kategori ağırlığı (klinik, kuyumcu, oto galeri, emlak yüksek; hobi, kişisel düşük),
takipçi eşiği, web sitesi varlığı, Places değerlendirme sayısı.

**Birleşik skor ağırlıklı çarpımdır, toplam değil:**

```
score = 100 * (activity/100)^0.30 * (potential/100)^0.40 * (capacity/100)^0.30
```

Çarpım seçilmesinin sebebi: herhangi bir alt skor sıfıra yaklaştığında toplam çöker.
Ölü ama potansiyeli yüksek bir hesap toplamda iyi görünmemeli — hiç dönüşmez.

Etkileşim oranı için **mutlak eşik kullanma.** Sektör medyanları yıldan yıla düşüyor ve
kaynaklar arasında 10 kata varan fark var. Karşılaştırma daima aynı kategorideki taranmış
hesapların medyanına göre yapılır; kohort 5 hesabın altındaysa potansiyel alt skoru
hesaplanmaz, hesap `watch` olur.

## 5. Denetim bulguları

Her bulgu deterministik bir kuraldan doğar. LLM bulgu icat etmez, sadece var olan bulguları
ajans diline çevirir ve önceliklendirir.

| Kural | Eşik | Ağırlık |
|---|---|---|
| Reels yok | 90 günde Reels oranı < %10 | kritik |
| Yorum yanıtsız | yanıtsız yorum oranı > %60 | yüksek |
| Bio'da dönüşüm yolu yok | link + telefon + CTA üçü de yok | yüksek |
| Kadans düzensiz | en uzun sessizlik > 14 gün | orta |
| CTA'sız caption | CTA içeren gönderi oranı < %20 | orta |
| Hashtag tekrarı | aynı hashtag seti gönderilerin > %70'inde | düşük |
| Görsel tutarsızlık | baskın renk kümesi 5'ten fazla, palet tutarsız | düşük |

Görünürlük skoru bu bulguların ağırlıklı cezasıdır, 100'den düşülür.

## 6. LLM katmanı

**Haiku 4.5** — tek çağrıda 30 gönderi: içerik sütunu sınıflandırma, ton etiketi, görsel
kalite notu, CTA tespiti. Çıktı katı JSON, şema Pydantic ile doğrulanır.

**Sonnet 5** — girdi: metrikler + bulgu listesi + rakip kohort istatistikleri. Çıktı: rapor
metni ve erişim mesajı taslağı. Sistem promptu cache'lenir.

Prompt'lar `api/llm/prompts/` altında versiyonlu dosyalar olarak durur, koda gömülmez.

## 7. API yüzeyi

```
POST /discovery/run          Places taraması başlat            → job_id
GET  /businesses             filtre: status, category, min_score
GET  /businesses/{id}        snapshot geçmişi + son skor
POST /businesses/{id}/audit  derin denetim kuyruğa al          → job_id
GET  /audits/{id}            bulgular + skor + pdf linki
PATCH /outreach/{id}         durum güncelle
GET  /jobs/{id}              kuyruk durumu
GET  /stats                  panel üst şeridi: taranan, nitelikli, rapor, aylık maliyet
```

Uzun süren her iş kuyruğa gider, endpoint anında `job_id` döner. Arayüz `/jobs/{id}` ile
yoklar. Senkron scraping çağrısı yasak.

## 8. Faz planı

**Faz 1 — iskelet.** Repo, docker-compose (postgres + redis), migration, `/stats` ve
`/businesses` uçları sahte veriyle, panel kabuğu. Bitiş kriteri: panel boş listeyi çiziyor.

**Faz 2 — veri.** Places adaptörü, IG adaptörleri, snapshot yazımı, 7 günlük cache.
Bitiş kriteri: tek komutla 20 işletme keşfedilip snapshot'ı alınıyor.

**Faz 3 — skorlama.** Triyaj motoru, kohort medyanı, durum atama. LLM yok.
Bitiş kriteri: 100 hesap taranıp panelde skorlarıyla listeleniyor.

**Faz 4 — denetim.** Bulgu kuralları, Haiku sınıflandırma, Sonnet sentez, maliyet kaydı.
Bitiş kriteri: bir hesap için bulgu listesi ve rapor metni üretiliyor.

**Faz 5 — çıktı.** PDF şablonu, erişim mesajı, outreach durum takibi.
Bitiş kriteri: PDF indiriliyor, mesaj taslağı kopyalanabiliyor.

**Faz 6 — sertleştirme.** 180 günlük silme cron'u, rate limit, e2e testler, maliyet alarmı.

Faz atlanmaz. Her fazın bitiş kriteri `docs/TASKS.md` içinde bir kutu olarak durur.
