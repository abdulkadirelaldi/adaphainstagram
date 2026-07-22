# Radar — tasarım dili

Panelin tek işi var: **hangi hesabın rapora gideceğine karar verdirmek.** Bu belgedeki her
karar o işe hizmet ettiği için var. Estetik bu işlevden doğar, üstüne giydirilmez.

Ham renk değerlerinin tek kaynağı `web/styles/tokens.css`. `web/app/` ve `web/components/`
altında çıplak hex bulunmaz.

---

## 1. Verilen token sistemine eleştiri

Başlangıç token sistemi sağlamdı; dört yerde eksikti. Üçünü kapattım, birini ölçtüm ve
dokunmadım.

**a) Palette dört ağırlık seviyesini karşılamıyordu.** SPEC §5 bulguları dört ağırlığa ayırıyor
(kritik · yüksek · orta · düşük), elde iki sinyal rengi var — patina ve oksit. Dördü ikiye
sıkıştırmak sahte eşitlik üretir. Karar: **ağırlık kromatik olarak kodlanmaz.** Oksit yalnızca
kritikte görünür; kalan üç seviye sıralama ve tipografik ağırlıkla ayrışır. Renk bir ölçü
birimi olarak kalır, kategori etiketine dönüşmez.

**b) Odak tokeni yoktu.** Vurgu rengi yasak, gölge yok, yarıçap ~0. Verilen altı değerin
hiçbiri klavye odağını çizemiyordu, ama kapsam sınırları "klavye odağı görünür olacak" diyor.
Eklendi: `--color-odak`, mürekkeple 2px halka + 2px kağıt ofseti. Yeni renk üretmedim.

**c) Kohort rayı ile "iki skor" uyarısı çelişiyordu.** Bkz. §5 — ayrı başlık hak ediyor.

**d) `kurşun` için ölçüm.** Sezgim zayıf olduğu yönündeydi; ölçtüm, **4.63:1** çıktı, AA'yı
geçiyor. Değiştirmedim. Tek kısıt: 13px altında ve rakamlarda kullanılmaz.

Ölçülen kontrastlar (kağıt `#FBFBF9` üstünde):

| token | değer | oran | rol |
|---|---|---|---|
| mürekkep | `#17191B` | 17.01:1 | ana metin, tüm rakamlar |
| kurşun | `#6E7377` | 4.63:1 | ikincil metin — 13px ve üstü |
| çizgi | `#E4E5E2` | 1.22:1 | ayraç; bilgi taşımaz, taşımamalı |
| patina | `#1F6F63` | 5.77:1 | skor sinyali |
| oksit | `#A6402E` | 5.97:1 | yalnızca kritik bulgu |

---

## 2. İleri taşınan eksen: renk bir skala oldu

**Değişiklik:** patina tek düz bir değerden, SPEC §1'in eşiklerine bağlanmış **üç duraklı
ölçülmüş bir skalaya** dönüştü.

```
--color-skor-elendi     #6E9A92   < 40    kağıda 3.03:1
--color-skor-izlemede   #3F857A   40–69   kağıda 4.18:1
--color-skor-nitelikli  #1F6F63   ≥ 70    kağıda 5.77:1
```

**Gerekçe.** Brief "renk bu projede marka öğesi değil, ölçü birimidir" diyor. Tek bir düz
değer bunu ancak *söyleyebilir*: "bu bir skordur" der, "bu skor şu kadardır" diyemez. Ölçü
birimi olmak demek büyüklüğü taşımak demektir. Tek hue içinde koyuluk skalası bunu yapar ve
ikinci bir renk getirmez — disiplin bozulmaz, sadece hak ettiği işi yapar.

Koyuluğun yönü kasıtlı: **koyuluk adaylıkla artar.** Nitelikli satırlar sayfada daha ağır
basar, göz listede doğal olarak onlara akar. Elenmiş satır silinmez ama öne çıkmaz.

**Kritik ölçüm ve sonucu.** Skalanın komşu durakları birbirine yalnızca **1.38:1**. Yani renk
üç bandı **tek başına ayırt ettirmiyor.** Bunu iddia etmek yerine ölçtüm ve kodlamayı üçe
çıkardım:

| eksen | ne kodlar | tipi |
|---|---|---|
| raydaki konum | skorun büyüklüğü | sürekli — **birincil** |
| çentik yüksekliği | bant (8px · 13px · 18px) | ayrık |
| renk durağı | bant | ayrık — **ikincil** |

Üç eksenin ikisi kromatik değil; renk körlüğünde ve gri baskıda panel bilgi kaybetmez.

**İkinci karar: rakam daima mürekkeptir.** Renk yalnızca raydaki dolu çentikte yaşar. Skoru
banda göre renklendirmek elendi durağını 3.03:1'e düşürürdü — okunabilirliği bant kodlamasına
feda etmek, ölçüm aletinde kabul edilemez. Rakam 17.01:1'de kalır, renk 3:1 grafik eşiğinin
geçerli olduğu yere taşınır. "Renkli olan tek şey skordur" kuralı korunur: renk hâlâ yalnızca
skor hücresinde, üstelik tam olarak ölçüm işaretinin üstünde.

---

## 3. Token'lar

Tam liste ve yorumları: `web/styles/tokens.css`. Özet:

**Tipografi.** İki rol, tek katı kural: **bu uygulamada hiçbir sayı sans yüzle dizilmez.**
Takipçi, skor, yüzde, tarih, para — hepsi `.sayi` (IBM Plex Mono, `tabular-nums`). Arayüz
Archivo. Tabular figürler sütun hizasını korur; satırlar arasında rakamlar kaymaz. Arayüze
alet hissini veren tek disiplin budur.

Ölçek: `mikro` 11 · `küçük` 12 · `gövde` 13 · `orta` 15 · `büyük` 20 · `rakam` 28.
Altı boy yeter; ara boy üretilmez.

*Bağlama notu:* font aileleri (`--font-arayuz`, `--font-sayi`) `@theme`'de değil `:root`'ta
durur (Tailwind v4 kullanılmayan `@theme` değişkenini tree-shake ediyordu) ve `next/font`
değişkenleri `<html>`'e verilir; body'de olsalardı `:root` token'ları onları çözemez, tüm
sayılar sessizce sans yüze düşerdi. Bu bir kez kırıldı, ölçülüp düzeltildi.

**Boşluk.** 4px taban. Yalnızca `1 · 2 · 3 · 4 · 6 · 8 · 12 · 16` adımları kullanılır.
Minimal yön hatasız aralık ister — ara değer üretmek ritmi bozar.

**Yarıçap.** Varsayılan `0`. Tek istisna ray ucu `1px`.

**Ölçü.** sol ray 208px · satır 44px · kohort rayı 132×20px.

---

## 4. İmza öğesi — kohort rayı

Skor hücresi çıplak bir sayı ya da rozet değil. Her hücrede **sabit bir 0–100 yatay ray**
durur. Taranmış kohortun tüm skorları bu rayda soluk çentikler, o satırın skoru dolu çentik.
Hiçbir skor tek başına okunmaz; daima kohortun içindeki yeriyle okunur.

Bu süs değil, ürünün tezi. SPEC §4 açıkça diyor: *"Etkileşim oranı için mutlak eşik kullanma.
Karşılaştırma daima aynı kategorideki taranmış hesapların medyanına göre yapılır."* Mutlak eşik
yanıltıcıdır, anlamlı olan görece konumdur. Ray tam olarak bunu gösterir.

**Ray asla veriye göre ölçeklenmez.** 0–100 sabittir. Ölçeği veriye uydurmak, karşılaştırmayı
imkânsız kılar — aletin taksimatı kaymaz.

**Kohort 5'in altındaysa çentikler çizilmez.** SPEC §4 gereği bu durumda potansiyel alt skoru
hesaplanmaz ve hesap `watch` olur. Ray boş taşıyıcı olarak durur, erişilebilir etiketi
"kohort 5 hesabın altında, karşılaştırma yapılmadı" der. Olmayan karşılaştırmayı çizmeyiz
(CLAUDE.md kural 7'nin ruhu). *Not: Faz 1 sahte verisinde her kategoride tek hesap var, bu
yüzden çentikler henüz görünmez — doğru davranış budur; gerçek tarama (Faz 2+) kohortları
doldurunca çentikler belirir.*

**Kohort kaynağı filtreden bağımsızdır.** `/businesses` sayfalı ve filtreli gelir; ama kohort
"aynı kategorideki taranmış tüm hesaplar" olmalı, yoksa `status=qualified` filtresi altında ray
yalnızca qualified skorları gösterir ve görece konum yanıltıcı olur. Bu yüzden panel kohortu
**ayrı, filtresiz bir istekten** besler (`useKohortKaynagi`, tek istek, 30s cache). Sınır:
`limit` üst sınırı 200; bunu aşan bir kohort kaynağı eksik kalır — Faz 1'de sorun değil, kalıcı
çözüm bir kategori-dağılım ucu ister (docs/TASKS.md `## Bloke`).

**Anahtar bir kez gösterilir.** Skor sütunu başlığının altında 0 · 40 · 70 · 100 taksimatı
duran sabit bir ray anahtarı var. Böylece her satırda bant etiketi tekrar etmeye gerek kalmaz.

Cesaret buraya harcandı. Gerisi sessiz.

---

## 5. İki skor — asla karıştırılmaz

Panelde ters yönde çalışan iki skor var. Bu, arayüzün en kolay yapacağı hata.

| | yön | anlamı |
|---|---|---|
| **Triyaj skoru** | ↑ yüksekse **iyi** | güçlü aday, derin denetime gider |
| **Görünürlük skoru** | ↓ düşükse **kötü** | hesap kötü yönetiliyor (SPEC §5 cezaları) |

Kurallar:

1. İkisine de **asla "skor" denmez.** Her görünümde tam adıyla yazılır: "Triyaj skoru",
   "Görünürlük skoru".
2. **Kohort rayı yalnızca triyaj skoruna aittir.** Görünürlük skoruna aynı ray formunu vermek
   ters yönlü iki ölçeği görsel olarak eşitler — imza öğesi tam da uyardığı hatayı üretirdi.
   Görünürlük skoru denetim görünümünde ayrı bir form ve açık yön ifadesiyle sunulur.
3. Aynı ekranda yan yana gösterilirlerse yön **metinle** belirtilir; okurun çıkarmasına
   bırakılmaz.

Eşikler tek yerde durur: `web/lib/skor.ts` (`ESIK_IZLEMEDE = 40`, `ESIK_NITELIKLI = 70`,
`ASGARI_KOHORT = 5`). Bileşenlerde sabit sayı yazılmaz.

**Bant `score`'dan değil `status`'tan gelir.** Sözleşmede (`openapi.yaml`) `score` ve `status`
ayrı alanlardır. SPEC §4 gereği kohort 5 hesabın altındaysa potansiyel hesaplanmaz ve hesap
skoru ne olursa olsun `watch` olur — yani mutlak skor eşiği (`skorBandi`) yanıltıcı olabilir.
Bu yüzden hücrenin rengi ve çentik yüksekliği **daima `status`'tan** türetilir; `score` yalnızca
raydaki konumu belirler. `status` yokken (henüz durum atanmamış) `skorBandi` yalnızca yedektir.
Skor null ama status varsa (kohort<5) rakam yerine yarım tire durur, yanında status etiketi
(“İzlemede”) sözle söylenir — ray konumu olmadığından tek işaret budur.

---

## 6. Yerleşim

**Satır başına kart yok.** Kenarlıklı yoğun satırlar, tam genişlik tablo, ince sol ray.
Gölge yok. Ayrım tek saç teli çizgiyle yapılır.

**Sol ray (208px).** Ürün adı + bölümler. Faz 1'de tek gerçek bölüm var; **ölü bağlantı
konmaz.** Bölümler inşa edildikçe eklenir.

**Keşif çubuğu (en üst).** Üst şeridin de üstünde ince bir eylem satırı: keşif sorgusu +
bölge (varsayılan Samsun) + en fazla (opsiyonel) + **Tara** düğmesi. Kart değil, alttan tek saç
teli çizgiyle ayrılır; filtre şeridiyle aynı alan/tipografi dilini paylaşır. Tarama sürerken
form kilitlenir ve çubuğun sağ ucunda durum belirir (bkz. §7 job yoklama). Buton metni akış
boyunca tek fiili korur: **Tara → Taranıyor → Tarama bitti.** İş bir eylemi tetikler ama sonucu
insan okur; çubuk kendini kutlamaz.

**Üst şerit.** SPEC §7 `/stats`: taranan · nitelikli · rapor · aylık maliyet. Dört ölçü, tek
satır, dikey çizgilerle ayrılmış. Rakam iri mono, etiket `mikro` versal kurşun. Şerit veri
yokken de **yerini korur** — yükleme bittiğinde düzen zıplamaz.

**Tablo.** Sütunlar: İşletme (ad + `@handle`) · Kategori · Değerlendirme · Keşfedildi · Triyaj
skoru. Genişlikler sabit (`colgroup`); veri gelince başlık kaymaz. Satır 44px — yoğun ama
rahat. Değerlendirme sağa dayalı mono (Places yorum sayısı, `rating_count`); Keşfedildi mono
tarih.

Bu sütunların **hepsi `openapi.yaml` `Business` şemasının gerçek alanlarıdır.** FE-1'de
konmuş "Takipçi" ve "Son gönderi" sütunları sözleşmeye aykırıydı: takipçi `snapshots`,
gönderi tarihi `posts` tablosunda; `Business`'ta ikisi de yok. FE-2'de sözleşmeye uyduruldu.

**Ölçmediğimiz hiçbir şey sütun olamaz.** Erişim, gösterim, kaydetme, profil ziyareti,
demografi bu sistemde yok ve arayüze giremez (CLAUDE.md kural 7). Takipçi/gösterim gibi
metrikler mock veriye bile eklenmez.

**Filtreler.** `status` · `category` · `min_score` — adları ve değer kümeleri `openapi.yaml`
`/businesses` query parametreleriyle birebir. **Filtre durumu URL query string'inde yaşar**
(tek gerçek kaynak): sayfa yenilenince kaybolmaz, paylaşılabilir, geri tuşuyla gezinilir.
Bileşen yerel filtre state'i tutmaz; `router.replace` ile URL'i yazar (geçmişi kirletmez).
Filtre değişince sayfa başa döner (`offset` sıfırlanır). Şeridin sağında canlı “N aday” sayacı
ve filtre varsa “Filtreleri temizle”.

**Sayfalama.** `limit` / `offset`, yanıttaki `total` ile. Tek sayfa varsa hiç çizilmez.
“ilk–son / toplam” mono; Önceki/Sonraki uçlarda pasifleşir.

İki skorun ters yönü metinle uyarılır: filtre etiketi “En düşük **triyaj** skoru” — hangi skor
olduğu ve yönü (yüksek = iyi aday) baştan bellidir.

### Gazete tuzağı

Verilen yön (saç teli ayraç, sıfır yarıçap, gölgesiz) kaçınılacaklar listesindeki "hairline
kurallı gazete düzeni"ne tehlikeli biçimde yakın. Ayrım şurada: gazetede çizgi **dekoratif**,
tipografi editöryel, hiyerarşi serif ağırlıklı. Burada çizgi **yalnızca veri satırlarını
ayırdığı yerde** var, hiyerarşiyi mono rakamlar taşıyor ve hizayı ray kuruyor. Serif yok,
editöryel ölçü yok, süs kural yok. Çizgi bir şey ayırmıyorsa silinir.

---

## 7. Durumlar

Tablo üç durumu birinci sınıf çizer; hiçbiri baştan savma değildir. Durum tek bir tipli
birleşimle (`yukleniyor | hata | hazir`) verilir ve TanStack Query'nin `isPending` / `isError`
bayraklarından türer. Üçü de gerçek: ağ/CORS hatası hata durumunu, `items: []` boş durumu
tetikler. Sayfa değişiminde tablo boşalmasın diye önceki sayfa yeni gelene dek durur
(`placeholderData`).

**Boş.** Özür dilemez, davet eder. Dönen çark ya da illüstrasyon yok. Filtre boş sonuç
verdiğinde:
> Bu filtreye uyan aday yok.
> Filtreleri gevşetin ya da temizleyin. Keşif çalıştığında Samsun'daki işletmeler taranır ve
> skorlarıyla buraya düşer; nitelikli olanlar rayın sağ ucunda toplanır.

Faz 1'in çıkış kriteri budur: mock kaynağı boş diziye çevrildiğinde (`MOCK_ISLETMELER = []`)
panel çökmez, bu durumu çizer.

**Yükleniyor.** Dönen çark yok. Tablo başlığını ve satır yerlerini korur, skor hücrelerinde
çentiksiz boş raylar durur. Alet yüklenirken de aletin biçimindedir.

**Veri yok ≠ sıfır.** Bilinmeyen değer daima yarım tire (`—`), asla `0`. `web/lib/bicim.ts`
bunu tek yerden garanti eder.

**Hata.** Ne olduğunu ve ne yapılacağını söyler (“Liste yüklenemedi. Sunucuya ulaşılamadı.
Bağlantıyı kontrol edip yeniden deneyin.”). Hata kodu tek başına gösterilmez; bir yeniden-dene
eylemi verilebilir.

### Job yoklama durum makinesi (keşif işi)

Keşif taraması uzun bir iştir; uç anında `job_id` döner (senkron scraping yok, SPEC §7) ve
arayüz `GET /jobs/{id}`'i yoklar. `JobState` enum'unun **her değerinin görünür bir karşılığı
var** — kullanıcı işin nerede olduğunu tahmin etmez:

| durum | görünen | poll |
|---|---|---|
| `queued` | “Kuyrukta…” | sürer |
| `running` | “Taranıyor” + ilerleme çubuğu (`processed/total`) | sürer |
| `done` | “Tarama bitti · N işletme, M snapshot” + Kapat | **durur** |
| `error` | “Tarama başarısız. {mesaj}” + Tekrar dene | **durur** |

**Poll disiplini.** Yoklama aralığı yalnızca `queued`/`running` iken çalışır; `done` ya da
`error`'a düşünce **durur** — süresiz istek yok. Bu, maliyet disiplininin arayüz tarafındaki
karşılığıdır (`CLAUDE.md`): boşa dönen bir poll bile israftır.

**İş bitince tablo tazelenir.** `done` olduğunda aday listesi, üst şerit ve kohort kaynağı
sorguları geçersizleştirilir; tablo yeni DB verisini kendiliğinden çeker. Kullanıcı elle
yenilemez.

**İlerleme dürüsttür.** `total` bilinmiyorsa (null) sahte bir yüzde çizilmez — yalnızca işlenen
sayı gösterilir. Ölçmediğini iddia etme kuralının (CLAUDE.md kural 7) ilerleme çubuğundaki
karşılığı budur.

**Hata rengi yok.** Keşif/yoklama hataları mürekkeple yazılır, oksitle değil — oksit yalnızca
kritik denetim bulgusuna ayrılmıştır (§1). Operasyon hatası bir bulgu değildir; renkli olan tek
şey skordur.

---

## 8. Metin

Türkçe, cümle düzeni, kısa. Butonlar fiille başlar ve akış boyunca **aynı kelimeyi korur**:
"Rapor üret" diyen düğme "Rapor üretildi" bildirimi doğurur, "Rapor oluşturuldu" değil.

Yasak: emoji, gradient, yuvarlak rozet yığınları, "AI destekli" tarzı pazarlama cümleleri.
Bu panel üç kişilik bir ajansın her gün içinde yaşadığı bir alet; kendini satmasına gerek yok.

---

## 9. Hareket

Neredeyse yok. Tek geçiş: tarama bittiğinde listeye düşen satır — 260ms, 2px yukarıdan,
opaklıkla. Başka hiçbir yerde animasyon yok. `prefers-reduced-motion: reduce` tüm süreleri
0.01ms'e indirir.

---

## 10. Kapsam

Hedef **1440px** masaüstü, **1024px**'e kadar zarifçe bozulur. Mobil v1 kapsamı dışında.

Yalnızca açık tema. Ama **tüm renkler CSS değişkeni** olarak tanımlı — koyu tema sonradan
`web/styles/tokens.css` üstünde tek dosyalık iş.

Klavye odağı her etkileşimli öğede görünür (`:focus-visible`, 2px mürekkep halka + 2px ofset).
Fare tıklamasında halka çıkmaz.
