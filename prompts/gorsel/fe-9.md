# [FRONTEND] FE-9 — kurumsal görsel yenileme (lacivert, açık+koyu tema)

Sen Radar projesinin **frontend** ajanısın. `CLAUDE.md`'yi oku. Sadece `web/**` ve
`docs/DESIGN.md` altına yazarsın. **Bu bir görsel yenileme — işlevsellik değişmez**, yalnız
tasarım dili.

## GÖREV FE-9 — editorial dili "lacivert kurumsal SaaS"a çevir

**Yön (kullanıcı seçti):** **Lacivert kurumsal** + **açık ve koyu tema**. Mevcut "gazete/
editorial" estetiği (kırık-beyaz kağıt, mürekkep/kurşun/patina, 13px sıkı tipografi, saç-teli
ayraçlar) yerine: **modern, şık, ferah, kurumsal, profesyonel** bir dashboard.

- Zemin: nötr gri (açıkta ~`#f4f6f8`), kartlar beyaz + **yumuşak gölge** + yuvarlak köşe.
- Vurgu: **lacivert** (~`#1e3a5f`). Metin: ana koyu (~`#0f172a`) / ikincil gri (~`#64748b`).
- **Ferah:** cömert boşluk (whitespace), rahat satır yüksekliği, net tipografi hiyerarşisi.
  13px sıkışıklığı bırak; okunur, dengeli ölçek.
- **Koyu tema:** her token'ın açık **ve** koyu değeri olsun; `prefers-color-scheme` +
  (varsa) kullanıcı toggle'ı. İki temada da kontrast AA.

**Oku:** `docs/DESIGN.md` (mevcut dil + korunacak ilkeler — özellikle §5 iki-skor, §4 kohort
rayı, §7 durumlar). `web/styles/tokens.css` (token tek kaynağı). `docs/SPEC.md` §1 (skor
eşikleri 40/70).

**Dokunabileceğin dosyalar:** `web/**`, `docs/DESIGN.md`

**Yapılacaklar:**
- **Token sistemini yenile** (`tokens.css` tek kaynak): renk (açık+koyu), tipografi ölçeği,
  boşluk, **gölge**, yarıçap. Bileşenlerde çıplak `#hex` **yok** — hepsi token.
- **Bileşenleri yeniden giydir**, yeniden yazma: üst şerit (istatistik kartları — büyük
  okunur sayılar), aday tablosu (rahat satır, hover, sıralama), filtreler, keşif çubuğu,
  denetim drawer, bulgu listesi (önem hiyerarşisi), PDF/kopyala/durum kontrolleri, boş/
  yükleniyor/hata durumları.
- **Maliyet alarmı göstergesi** (FE-8) kurumsal dille — dikkat çeken ama panik olmayan uyarı.
- Modern, kurumsal bir tipografi seç; **jenerik "AI slop" fontlardan kaçın** (Inter/Roboto/
  Arial/sistem-varsayılan klişesi). Sayılar `tabular-nums` ile hizalı.

**Korunacak (değiştirme):**
- **İki skor asla karışmaz** (DESIGN §5): triyaj skoru (yüksek=iyi) ve görünürlük skoru
  (denetim, ceza) görsel olarak ayrı kalır.
- **Skor bantları renk-dışı ikinci işaretle** de kodlanır (renk körlüğü — mevcut ray/çentik
  yaklaşımı sürer). Eşikler 40/70 (SPEC §1).
- **Kohort<5** → skor "—" + status etiketi (yanıltıcı skor gösterme).
- **Erişim taslağı yalnız kopyalanır**, "gönder" eylemi hiçbir yerde yok (hukuki sınır).
- Erişim/gösterim/kaydetme/demografi gösteren hiçbir alan yok (kural 7).

**Kabul kriterleri:**
- `npm run build` + `npx tsc --noEmit` + `npx next lint` sıfır hata.
- **Açık + koyu tema** çalışıyor: `prefers-color-scheme` değişince (ve toggle varsa) tüm yüzeyler
  doğru; iki temada da metin kontrastı AA (ana metin ≥ 4.5:1).
- Skor bantları **her iki temada** renk-dışı işaretle ayırt ediliyor.
- `git grep -nE "#[0-9a-fA-F]{6}" -- web/app web/components` boş (çıplak hex yalnız token dosyasında).
- `git grep -niE "gönder|send" -- web/` yalnız taslak/kopyala/durum bağlamında; mesaj gönderen kod yok.
- Yasak-metrik grep boş.
- **Canlı smoke (fixture backend ayakta, `localhost:3000`):** üst şerit + tablo + filtre +
  denetim drawer + PDF indir + taslak kopyala + durum güncelleme akışı **çalışıyor** (headless
  ya da elle doğrula) — görsel yenileme hiçbir akışı kırmadı.
- `docs/DESIGN.md` yeni token sistemini + açık/koyu tema kararını + korunan ilkeleri (iki-skor,
  renk-dışı bant, kohort<5, gönderme-yok) belgeliyor.

**Kapanış:** `docs/TASKS.md`'de FE-9'u `## Biten`'e taşı (önce/sonra kısa not: hangi bileşenler
yenilendi, tema nasıl kuruldu). `docs/DESIGN.md` güncel. `git add web/ docs/DESIGN.md
docs/TASKS.md`, `fe:` prefix'iyle commit'le. Sonra orkestra şefine "FE-9 görsel yenileme bitti,
panel kurumsal/ferah, açık+koyu tema" de.
