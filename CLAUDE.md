# Radar — Kıyı Medya aday tarama ve denetim sistemi

Bu dosyayı her Claude Code oturumu otomatik okur. Dört ajan aynı repoyu paylaşır ama
birbirinin context'ini **görmez**. Koordinasyon sadece bu repodaki dosyalar üzerinden olur.

## Ürün tek cümlede

Samsun'daki işletmelerin halka açık Instagram hesaplarını tarar, hangilerinin Kıyı Medya'ya
iyi aday olduğunu skorlar, nitelikli olanlar için ajans kalitesinde bir denetim raporu ve
kişiselleştirilmiş erişim mesajı üretir.

Detaylı ürün ve teknik şartname: `docs/SPEC.md`. Açık görevler: `docs/TASKS.md`.

## Ajanlar ve dosya sahipliği

Sahiplik mutlaktır. Kendi dizinin dışına **yazma**. Okumak serbest.

| Ajan | Yazabildiği yer | Rolü |
|---|---|---|
| Orkestra şefi | `docs/**`, `prompts/**`, `CLAUDE.md` | Planlar, görev yazar. Kod yazmaz. |
| Backend | `api/**`, `docs/openapi.yaml` | Veri toplama, skorlama, LLM, PDF, REST API |
| Frontend | `web/**`, `docs/DESIGN.md` | Panel arayüzü, rapor görünümü |
| Güvenlik & test | `tests/**`, `.github/**`, `docs/REVIEW.md` | Test, statik analiz, gizlilik ve maliyet denetimi |

Başka bir ajanın dizininde sorun görürsen **düzeltme**. `docs/TASKS.md` içine `## Bloke`
başlığı altında not düş, sahibine bırak.

## Değişmez kurallar

1. **`git add -A` yasak.** Sadece kendi dizinini stage et: `git add api/` gibi. Dört oturum
   aynı anda commit atabilir.
2. **Commit prefix'i zorunlu:** `be:`, `fe:`, `sec:`, `docs:`.
3. **Sözleşme önce gelir.** Backend bir endpoint yazmadan önce `docs/openapi.yaml`'ı günceller
   ve commit'ler. Frontend tipleri o dosyadan üretir, elle tip yazmaz.
4. **Sır yok.** API anahtarları sadece `.env` içinde, `.env.example` güncel tutulur.
   Kod, log, test fixture veya commit içinde hiçbir anahtar geçmez.
5. **Görev bitince `docs/TASKS.md` güncellenir.** Bitmiş görev `## Biten` altına taşınır,
   tek satır sonuç notuyla. Bu dosya ajanlar arası tek senkronizasyon noktasıdır.
6. **Gerçek veriyle test yok.** Testler `tests/fixtures/` içindeki sabit JSON'ları kullanır.
   Hiçbir test canlı Instagram veya Apify çağrısı yapmaz.
7. **Ölçmediğini iddia etme.** Erişim, gösterim, kaydetme, profil ziyareti ve demografi
   verisi bu sistemde **yoktur**. Bu metrikler ne veritabanına, ne rapora, ne arayüze girer.

## Teknoloji

Backend: Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, PostgreSQL 16, Redis + arq,
httpx, Pydantic v2, Anthropic SDK, Playwright (PDF).
Frontend: Next.js 15 (App Router), TypeScript strict, Tailwind, TanStack Query.
Test: pytest + pytest-asyncio, ruff, mypy, Playwright e2e.

## Maliyet disiplini

Bu sistemin rekabet avantajı düşük marjinal maliyet. Her ajan bunu korumakla yükümlü.

- Aynı hesap 7 gün içinde tekrar kazınmaz. Redis cache zorunlu.
- Toplu iş: gönderi başına ayrı LLM çağrısı **yasak**. Tek çağrıda batch'le.
- Post başına sınıflandırma `claude-haiku-4-5`, rapor sentezi `claude-sonnet-5`.
- Sistem promptu ve benchmark tablosu prompt caching ile sabitlenir.
- Her denetim `audits.llm_cost_usd` alanına gerçek maliyetini yazar. Bu alan boş kalamaz.

## Hukuki sınırlar

- Toplanan veri yalnızca oturum açmadan erişilebilen halka açık veridir.
- Kişisel hesaplar taranabilir ama rapor üretilmez; sadece işletme hesapları rapora girer.
- Dönüşmeyen adayın verisi 180 gün sonra otomatik silinir. Bu bir cron görevidir, opsiyonel değil.
- Sistem **hiçbir koşulda otomatik mesaj göndermez.** Mesaj taslak olarak üretilir, gönderme
  kararı insandadır. `outreach` kaydı `draft` durumunda doğar.
