# Radar — tasarım dili

Panelin tek işi var: **hangi hesabın rapora gideceğine karar verdirmek.** Bu belgedeki her
karar o işe hizmet ettiği için var.

Ham renk değerlerinin tek kaynağı `web/styles/tokens.css`. `web/app/` ve `web/components/`
altında çıplak hex bulunmaz.

> **Görsel yön (FE-9).** Panel önce editorial-minimal bir dille (kırık-beyaz kağıt, mürekkep/
> patina, 13px sıkı tipografi, saç-teli ayraç) kuruldu. FE-9'da **kurumsal lacivert SaaS**
> diline çevrildi: nötr zemin + beyaz kartlar + yumuşak gölge + ferah boşluk, lacivert vurgu,
> açık **ve** koyu tema. İşlevsellik değişmedi — aşağıdaki korunan ilkeler (iki-skor, kohort
> rayı, renk-dışı bant, kohort<5, gönderme-yok) FE-9'da bire bir sürdürüldü.

---

## 1. Renk sistemi (açık + koyu)

Altı ham renk yerine **anlamlı yüzey/metin/vurgu katmanları** var; her token'ın açık **ve** koyu
değeri `tokens.css`'te. Bileşen tek token kullanır (`bg-yuzey`, `text-metin`…), tema değişince
`--tk-*` değeri değişir — bileşende `dark:` varyantı yok, renk mantığı tek yerde.

| token | rol | açık | koyu |
|---|---|---|---|
| `zemin` | uygulama arka planı | `#eef2f7` | `#0b1220` |
| `yuzey` | kart / panel / girdi | `#ffffff` | `#131c2e` |
| `yuzey-2` | ikincil yüzey · satır hover · başlık | `#f5f8fc` | `#1c2740` |
| `metin` | ana metin | `#0f172a` | `#eef2f7` |
| `metin-2` | ikincil metin | `#56657a` | `#9aa8bd` |
| `ayrac` | kenarlık / ayraç | `#e2e8f0` | `#273349` |
| `marka` | lacivert · birincil eylem | `#1e3a5f` | `#4a78ac` |
| `marka-yumusak` | aktif nav · hover zemin | `#e9f0f7` | `#1b2942` |
| `uyari` | kritik bulgu + maliyet alarmı | `#b4341f` | `#f0796a` |

**Kontrast ölçüldü, AA sağlandı** (kağıt/koyu yüzey üstünde): ana metin 17.9:1 / 15.2:1;
ikincil metin 5.9:1 / 7.1:1; marka butonda beyaz 11.5:1 / 4.6:1; uyarı 6.1:1 / 6.2:1. Marka
koyu tema değeri (`#4a78ac`) hem beyaz metni AA'da tutacak hem koyu zeminde görünür kalacak
biçimde ölçülerek seçildi.

**Vurgu ölçülüdür.** Lacivert yalnızca eylem (buton, aktif bölüm, odak halkası) ve
kimliktedir. Skor rengi ve kritik uyarı ayrı hue'lardadır (aşağı) — marka onların yerini almaz.

---

## 2. Skor bandı — renk ikincil, konum birincil

Triyaj skoru üç banda ayrılır (SPEC §1: `< 40` elendi · `40–69` izlemede · `≥ 70` nitelikli).
Bant üç eksende kodlanır ve **renk yalnızca üçüncü eksendir**:

| eksen | ne kodlar | tipi |
|---|---|---|
| raydaki konum | skorun büyüklüğü | sürekli — **birincil** |
| çentik yüksekliği | bant (8 · 13 · 18 px) | ayrık — renk-dışı |
| renk durağı | bant (`skor-elendi/izlemede/nitelikli`) | ayrık — ikincil |

İki eksen kromatik değildir; **renk körlüğünde ve gri baskıda bant yine ayrışır.** FE-9'da skor
renkleri kurumsal palete taşındı (elendi nötr `#64748b`, izlemede teal `#0e7490`, nitelikli
`#0f766e`; koyu temada açıldı) ama üç-eksen kodlaması korundu; her iki temada da 3:1 grafik
eşiği aşıldı.

**Skor rakamı `floor` ile yuvarlanır, `round` ile değil.** Skor bir eşik göstergesidir (≥70,
≥40); `round(39.6)="40"` bir `rejected` satırı izlemede eşiğinde gösterirdi. `floor` daima
status bandıyla hizalı: gösterilen "70" gerçekten ≥70, "39" gerçekten <40'tır.

---

## 3. Tipografi ve ölçü

**Font: Manrope** (Google Fonts, latin-ext → Türkçe tam). Modern, ferah, humanist bir grotesk;
jenerik system/Inter/Roboto/Arial klişesinden uzak, kurumsal ve okunaklı. Tek aile, ağırlıklarla
hiyerarşi (400/500/600/700). Editorial dönemin "sayılar mono" disiplini bırakıldı; sayılar
arayüz fontuyla ama **`tabular-nums`** ile dizilir — sütun hizası korunur, ferah durur.

Ölçek (13px sıkışıklığı bırakıldı): `mikro` 12 · `küçük` 13 · `gövde` 14 · `orta` 16 ·
`büyük` 20 · `başlık` 24 · `rakam` 30. Satır yükseklikleri rahat.

**Yarıçap ve gölge kurumsal:** kart 12px, buton/girdi 8px; iki katmanlı yumuşak gölge
(`shadow-kart` yüzeyler, `shadow-yuzen` drawer). Editorial "sıfır yarıçap, gölge yok" kuralı
FE-9'da tersine döndü — yön kartlı, ferah, yumuşak.

**Boşluk ferah.** İçerik 24–32px kenar boşluğu, kartlar arası 16–24px, satır 56px. Cömert
whitespace kurumsal dilin belkemiği.

---

## 4. İmza öğesi — kohort rayı

Skor hücresi çıplak bir sayı ya da rozet değil. Her hücrede **sabit bir 0–100 yatay ray**
durur. O kategorinin skor **dağılımı** (çeyrekler) rayda soluk bir bant, o satırın skoru dolu
çentik. Hiçbir skor tek başına okunmaz; daima kohortun içindeki yeriyle okunur.

Bu süs değil, ürünün tezi. SPEC §4: *mutlak eşik yanıltıcıdır, anlamlı olan görece konumdur.*
Ray tam olarak bunu gösterir.

**Çeyrek bandı (FE-8).** Kaynak `GET /stats/categories` (BE-23): kategori başına **medyan +
Q1 + Q3**. Ray Q1–Q3 arası soluk bir bant (dağılımın orta %50'si) + medyan çizgisidir; o satırın
skoru dolu çentik. Üç sayıyla 200+ hesapta ölçeklenir, dağılımı nicel gösterir. `limit=200`
istemci-türetimi söküldü (FE-3-B1).

**Ray asla veriye göre ölçeklenmez** (0–100 sabit). **Kohort 5'in altındaysa bant çizilmez**
(SPEC §4 → `score_median` null); hesap `watch`, ray boş, skor hücresi "—" + status etiketi
gösterir. Olmayan karşılaştırmayı çizmeyiz.

---

## 5. İki skor — asla karıştırılmaz

Panelde ters yönde çalışan iki skor var. Arayüzün en kolay yapacağı hata bu.

| | yön | anlamı |
|---|---|---|
| **Triyaj skoru** | ↑ yüksekse **iyi** | güçlü aday, derin denetime gider |
| **Görünürlük skoru** | ↓ düşükse **kötü** | hesap kötü yönetiliyor (SPEC §5 cezaları) |

1. İkisine de **asla "skor" denmez** — her görünümde tam adıyla.
2. **Kohort rayı yalnızca triyaj skoruna aittir.** Görünürlük skoru denetim panelinde ayrı bir
   kartta, **yönü metinle** ("düşük skor kötü yönetim — tablodaki triyaj skorunun tersi") ve ray
   OLMADAN sunulur. Aynı ray formunu ikisine vermek imza öğesinin uyardığı hatayı üretirdi.
3. Eşikler tek yerde: `web/lib/skor.ts` (`ESIK_IZLEMEDE=40`, `ESIK_NITELIKLI=70`).

**Bant `status`'tan, ray konumu `score`'dan gelir.** Kohort<5'te skor eşiği yanıltıcı (SPEC §4)
olduğundan bant otoriter olarak backend `status`'undan türetilir; `score` yalnızca konumu verir.

---

## 6. Yerleşim

**Kurumsal dashboard.** Yüzey renginde ince sol gezinme + zemin renginde içerik. İçerik ferah
padding'li, dikey kart yığını. Aktif bölüm `marka-yumusak` zemin + `marka` metin. Sol rayda
**tema anahtarı** (güneş/ay ikonu — renk taşımaz, ikon + `aria-label` durumu söyler).

**Üst şerit — istatistik kartları.** SPEC §7 `/stats`: taranan · nitelikli · rapor · aylık
maliyet. Dört **kart** (beyaz yüzey, yumuşak gölge, yuvarlak, büyük okunur sayı). Veri yokken
yarım tire; kart yerini korur, düzen zıplamaz.

**Maliyet alarmı (SPEC §8).** `monthly_cost_alarm` true → maliyet kartı `uyari` kenarlığı +
rakam `uyari` + "Eşik aşıldı" metni. **Renk tek taşıyıcı değildir** — metin uyarıyı sözle de
söyler; renk körlüğünde de okunur. Alarm kapalıyken sessiz. Oksit/uyarı rengi §1'de ölçülü
biçimde iki yere ayrılmıştır: kritik bulgu + maliyet alarmı; maliyet disiplini ürünün merkezi
olduğundan eşik aşımı kritik bir sistem durumudur.

**Tablo.** Kart içinde: gri başlık şeridi, ferah satır (56px), **hover'da yüzey-2 zemin**,
tıklanabilir (klavye: `tabIndex`+Enter). Sütunlar `openapi` `Business` alanları: İşletme
(ad + `@handle`) · Kategori · Değerlendirme (`rating_count`) · Keşfedildi · Triyaj skoru.
Takipçi/gösterim gibi ölçülmeyen alanlar sütun olamaz (CLAUDE.md kural 7).

**Denetim paneli (drawer).** Satır seçilince sağdan gölgeli drawer (`shadow-yuzen`, 560px),
arkada hafif karartma örtü (`orten`), Esc/Kapat/tık-kapat. **Denetim yalnız nitelikli hesaba**
üretilir; değilse "Derin denetim" düğmesi yok, sebep açık. Görünürlük skoru kartı + bulgular +
rapor metni + PDF indir + erişim taslağı.

**Bulgu önem hiyerarşisi.** Bulgular öneme sıralı (kritik üstte, SPEC §5). **Yalnızca kritik
`uyari` (oksit) alır**; kalan üç seviye sıralama + önem etiketiyle ayrışır — kromatik kodlama
yok. Her bulgu iki katman taşır ve ayrı gösterilir: `detail` (deterministik tetik, daima dolu)
ve `message` (LLM ajans-dili, null olabilir). LLM bulgu icat etmez.

**PDF indir.** `pdf_path` null → düğme pasif + sebep ("hazır olduğunda"); dolu → binary indirir.
Boş alan hata gibi gösterilmez.

---

## 7. Erişim kaydı — kopyalanır ve izlenir, gönderilmez

Erişim mesajının iki eylemi vardır, ikisi de insan kararı: **kopyala** (metni al) ve **durumu
güncelle** (nerede kaldığını kaydet). "Gönder / DM at / e-posta yolla" **bilinçle yoktur** —
CLAUDE.md hukuki sınırı: sistem hiçbir koşulda otomatik mesaj göndermez, kayıt `draft` doğar.

**Durum takibi bir gönderim değildir.** `draft → sent → … → won/lost` (SPEC §3) bir select ile
insan tarafından güncellenir → `PATCH /outreach/{id}`. "Gönderildi"yi işaretlemek, bir insanın
mesajı **elle gönderip** kaydetmesidir. Sözleşme bunu yapısal sabitler (`OutreachUpdate` yalnız
`status`). Durum tam Türkçe adıyla okunur (renk tek taşıyıcı değil); `sent_at`/`replied_at`
sunucu damgaları gösterilir; geçersiz geçiş `422` → net hata, select eski değerinde kalır.

---

## 8. Durumlar

Üç durum birinci sınıf; hiçbiri baştan savma değil. Durum tipli birleşimle
(`yukleniyor | hata | hazir`) ve TanStack Query'nin `isPending`/`isError`'ından türer.

**Boş.** Özür dilemez, davet eder: "Bu filtreye uyan aday yok. Filtreleri gevşetin…". Dönen
çark/illüstrasyon yok.

**Yükleniyor.** Tablo başlığını ve satır yerlerini korur; skor hücrelerinde çentiksiz boş ray.

**Hata.** Ne olduğunu ve ne yapılacağını söyler; kod tek başına gösterilmez; yeniden-dene verilir.
Hata metinleri `uyari` değil `metin`/`metin-2` ile — uyari yalnızca kritik bulgu + maliyet
alarmına ayrıldı.

**Job yoklama durum makinesi.** Keşif/denetim işi uzun; uç anında `job_id`, arayüz
`GET /jobs/{id}` yoklar. `JobState`'in her değeri görünür: `queued` (Kuyrukta) · `running`
(Taranıyor + ilerleme) · `done` (sonuç + Kapat) · `error` (mesaj + Tekrar dene). **Poll
`done`/`error`'da durur** — süresiz istek yok (maliyet disiplini). İş `done` olunca liste +
üst şerit + kohort sorguları tazelenir. `total` null ise sahte yüzde çizilmez (kural 7).

**Denetim iki fazlı; yarım rapor hata değil.** Önce deterministik bulgular + skor, sonra LLM
sentezi (rapor + taslak + bulgu `message`). Null gelen alan "yapay zekâ sentezi tamamlanınca…"
der; deterministik kısım zaten tam gösterilir.

---

## 9. Metin

Türkçe, cümle düzeni, kısa. Butonlar fiille başlar ve **aynı kelimeyi korur**: "Kopyala →
Kopyalandı", "Tara → Taranıyor → Tarama bitti". Yasak: emoji, gradient, "AI destekli" pazarlama
cümleleri. Bu panel üç kişilik bir ajansın her gün yaşadığı bir alet; kendini satmaz.

---

## 10. Hareket

Ölçülü. Tema geçişi 120ms yumuşak (sert flaş yok). Satır hover renk geçişi, buton opaklık
geçişi. Tarama bittiğinde listeye düşen satır için tek giriş geçişi. `prefers-reduced-motion`
tüm süreleri 0.01ms'e indirir.

---

## 11. Tema (açık + koyu)

Her token'ın açık ve koyu değeri var. Tema üç kaynaktan gelir, öncelik sırasıyla:

1. **Kullanıcı seçimi** — sol raydaki anahtar; `<html>`'e `tema-acik`/`tema-koyu` sınıfı,
   `localStorage`'da kalıcı.
2. **Sistem tercihi** — kullanıcı seçmediyse `@media (prefers-color-scheme: dark)`.
3. **Varsayılan** — açık.

**FOUC yok:** tema, ilk boyadan önce `<head>`'deki küçük bir script ile `<html>`'e uygulanır.
Her iki temada da metin kontrastı AA; skor bantları renk-dışı işaretle (konum + çentik) ayrışır.

---

## 12. Kapsam ve korunan ilkeler

Hedef **1440px** masaüstü, **1024px**'e zarifçe bozulur. Mobil v1 dışı. Klavye odağı her
etkileşimli öğede görünür (`:focus-visible`, marka halkası).

FE-9 görsel yenilemesinde **değişmeden korunan** işlevsel ilkeler:

- **İki skor asla karışmaz** (§5) — triyaj (yüksek=iyi) ↔ görünürlük (düşük=kötü), yön metinle.
- **Skor bantları renk-dışı ikinci işaretle** kodlanır (§2) — renk körlüğü; her iki temada.
- **Kohort<5 → skor "—" + status** (§4) — yanıltıcı skor gösterilmez.
- **Erişim taslağı yalnız kopyalanır** (§7) — "gönder" eylemi hiçbir yerde yok (hukuki sınır).
- **Ölçülmeyen alan yok** — erişim/gösterim/kaydetme/demografi hiçbir yerde (kural 7).
- **Renk tek taşıyıcı değil** — maliyet alarmı, önem, durum: renk + metin/ikon birlikte.
