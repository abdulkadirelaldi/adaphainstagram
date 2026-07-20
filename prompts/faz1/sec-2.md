# [GÜVENLİK & TEST] Faz 1 · SEC-2 — `.gitignore` sahipliği

Sen Radar projesinin **güvenlik & test** ajanısın. `CLAUDE.md`'yi oku.

## Sahiplik kararı

`docs/TASKS.md` "Araç konfigürasyonu sahipliği" tablosuna eklendi: **`.gitignore` artık
senin.** SEC-1-B3'te işaret ettiğin boşluğun sahibi sensin — repo hijyeni senin alanın.
Diğer ajanlar bir yol eklenmesi gerektiğinde `## Bloke`'ya yazar, kendileri eklemez.

## GÖREV SEC-2

**Amaç:** SEC-1-B3'ü kapatmak ve `.gitignore`'u bir kere doğru kurmak.

**Oku:** `docs/REVIEW.md` (kendi SEC-1-B3 bulgun), `docs/TASKS.md` `## Bloke`.

**Dokunabileceğin dosyalar:** `.gitignore`, `docs/REVIEW.md`, `tests/**`

**Yapılacaklar:**
- `.env.local` ve `.env.*.local` ekle — Next.js bunları standart kullanıyor ve `web/` artık
  var.
- Bir tur daha bak: `.next/`, `node_modules/`, `__pycache__/`, `.venv/` zaten var. Eksik
  kalmış başka sızıntı yolu var mı — `.DS_Store`, `*.pem`, `*.key`, coverage çıktıları,
  Playwright `test-results/`, Alembic'in ürettiği geçici dosyalar? Gerekçesiz kalabalık
  yapma, gerçekten bu repoda oluşabilecekleri ekle.
- **Regresyon testi yaz.** Bu bulgunun bir daha sessizce dönmemesi için `tests/` içine bir
  test ekle: repo kökünde `git check-ignore` ile `.env`, `.env.local`, `.env.production.local`
  yollarının yok sayıldığını doğrulasın. SEC-1'de ağ muhafızı için yaptığının aynısı —
  kuralı makineye devret.

**Kabul kriterleri:**
- `git check-ignore -v .env .env.local .env.production.local` üçü için de eşleşme dönüyor.
- Yeni regresyon testi geçiyor; `.gitignore`'dan `.env.local` satırını geçici olarak
  sildiğinde test **kırmızıya dönüyor** (testin gerçekten bir şey ölçtüğünün kanıtı —
  bunu doğrula, sonra satırı geri koy).
- `pytest` tamamen yeşil.
- `git status --porcelain` içinde izlenmeye aday `.env*` dosyası görünmüyor.
- `docs/REVIEW.md`'de SEC-1-B3 `FAIL` → `PASS`'a çevrildi, kanıt satırıyla.

**Kapanış:** `docs/TASKS.md`'de SEC-2'yi `## Biten` altına taşı ve `## Bloke` içindeki
SEC-1-B3 satırının sonuna `→ SEC-2 ile çözüldü` ekle.
`git add .gitignore tests/ docs/REVIEW.md docs/TASKS.md` ile stage et (`git add -A` yasak),
`sec:` prefix'iyle commit'le.

---

## Not — Docker kararı

Orkestra şefi kararını verdi: Faz 1 çıkış kriteri **yerel postgres@16 + redis** ve CI servis
konteyneri üzerinden doğrulanır. `docker-compose.yml` repoda kalır ama **doğrulanmamış**
sayılır; gerçek `docker compose up` doğrulaması Faz 6'ya alındı. CI'ını buna göre değiştirmene
gerek yok — zaten servis konteyneri kullanıyorsun, doğru yoldasın.
