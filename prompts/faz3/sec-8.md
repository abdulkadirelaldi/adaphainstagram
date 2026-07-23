# [GÜVENLİK & TEST] Faz 3 · SEC-8 — fixture'ı 100 hesaba genişlet, skor sinyallerini çeşitlendir

Sen Radar projesinin **güvenlik & test** ajanısın. `CLAUDE.md`'yi oku. Sadece `tests/**`,
`.github/**`, `docs/REVIEW.md` ve lint konfig dosyalarına yazarsın.

**Bu görev Faz 3 bitiş kriterini besliyor** (SPEC §8: "100 hesap taranıp panelde skorlarıyla
listeleniyor"). Skorlama motoru (BE-11) fixture içeriğinden bağımsız yazılabilir; sen 100-hesap
zeminini ve skorların **dağılmasını** sağlayan sinyal çeşitliliğini kurarsın.

## GÖREV SEC-8 — 100 hesaplık skorlama fixture'ı

**Amaç:** Places + profil fixture'larını ~100 hesaba çıkarmak ve SPEC §4'teki skor sinyallerini
öyle çeşitlendirmek ki skorlar tüm bantlara (`rejected`/`watch`/`qualified`) yayılsın ve kohort
mantığı test edilebilsin.

**Oku:** `docs/SPEC.md` §4 (triyaj skoru — aktiflik, potansiyel, kapasite sinyalleri; kohort
medyanı; kohort<5 kuralı) ve §1 (durum eşikleri). `tests/fixtures/README.md`, mevcut SEC-6
fixture'ların. `docs/TASKS.md` → "IG handle eşleme sözleşmesi" (genişletirken uy).

**Dokunabileceğin dosyalar:** `tests/**`, `docs/REVIEW.md`

**Yapılacaklar:**
- Places fixture'ını ~100 uydurma Samsun işletmesine çıkar. Handle eşleme sözleşmesi korunur
  (bir kısmı instagram URL'li → snapshot yolu, bir kısmı değil → NULL yolu; yanlış-pozitif
  tuzakları kalsın).
- **Kohort için kategori dağılımı:** bazı kategoriler **≥5 hesap** (kohort medyanı hesaplanır),
  en az bir kategori **<5 hesap** (kohort yetersiz → potansiyel hesaplanmaz, `watch` — SPEC §4).
  İkisini de test edebilmek için bilinçli kur; README'ye hangi kategori kaç hesap yaz.
- **Skor sinyallerini çeşitlendir** (SPEC §4'e göre profil/post fixture'larında):
  - *Aktiflik:* kimi hesap son 90 günde yoğun + kısa sessizlik (yüksek), kimi 0 gönderi (0),
    kimi uzun sessizlikli (orta). `posted_at`'leri buna göre dağıt.
  - *Potansiyel:* Reels oranı (düşük/yüksek `media_type` dağılımı), etkileşim (like/comment
    counts kategori içi farklı), CTA'lı/CTA'sız caption'lar, yorum yanıt izleri.
  - *Kapasite:* kategori ağırlığı (klinik/kuyumcu/oto/emlak yüksek; hobi/kişisel düşük),
    takipçi eşiği, website var/yok, `rating_count` dağılımı.
  - **Zaman fixture kararı:** `posted_at` gibi tarihler sabit ISO timestamp olsun; "bugün"e
    göreli tarih kullanma (testler `currentDate`'e bağlı olmamalı, tekrarlanabilir kalmalı).
    README'ye referans tarihini yaz — skorlama motoru (BE-11) 90 gün penceresini buna göre
    sabitleyebilsin. **Bu bir sözleşme:** BE-11'e referans "şimdi"nin fixture'da nasıl
    verildiğini net bildir.
- `apify_profile.json`'daki yasak alanlar (SEC-4/SEC-6) **korunur** — genişletirken silme.
- README'yi güncelle: 100 hesabın kategori dağılımı, kohort<5 kategorisi, skor-bandı hedefleri
  (kaç hesap rejected/watch/qualified olması bekleniyor), referans zaman.

**Yapmayacakların:**
- `api/`'ye dokunma; skorlama motorunu sen yazmazsın, yalnız veri + beklenti sağlarsın.
- Gerçek işletme/kişi verisi (kural 6 — sabit, sahte, tekrarlanabilir).
- Erişim/gösterim/kaydetme/demografi alanını normalize yola taşıma (yalnız Apify `raw` fixture'ında).

**Kabul kriterleri:**
- Places fixture ~100 işletme, geçerli JSON; kategori dağılımı README'de; en az bir kategori <5.
- Profil fixture'ları 100 hesabı kapsıyor (handle-anahtarlı yapı korunuyor), skor sinyalleri
  (aktiflik/potansiyel/kapasite) kategori ve hesap bazında **belirgin biçimde** çeşitli.
- Tarihler sabit ISO; göreli "bugün" yok; referans zaman README'de.
- `pytest` yeşil (mevcut kontrat/entegrasyon testleri genişletilmiş fixture'la hâlâ geçiyor);
  ağ kapalıyken de yeşil. `ruff`+`mypy` temiz.

**Kapanış:** `docs/TASKS.md`'de SEC-8'i `## Biten`'e taşı; backend'e "fixture 100 hesap, skor
sinyalleri çeşitli, referans zaman README'de — BE-11 skorlamayı 100 ile doğrulayabilir" not düş.
`git add tests/ docs/REVIEW.md docs/TASKS.md` (`git add -A` yasak), `sec:` prefix'iyle commit'le.
