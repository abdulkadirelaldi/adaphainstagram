import { expect, test } from "@playwright/test";

/**
 * Panel smoke (SEC-11-N1) — kritik akışın tarayıcıda kırılmadığını doğrular:
 * panel açılır → keşif tetiklenir → tablo dolar → bir denetim açılır.
 *
 * Ön koşul: panel ayakta (baseURL) ve backend **fixture modunda** (anahtarsız,
 * canlı çağrı yok). Kapsamlı değil; kritik yolun smoke'u. Ayrıntılı senaryolar
 * geliştirme sırasında ad-hoc headless ile doğrulanır.
 */
test("panel: keşif → tablo → denetim akışı kırılmıyor", async ({ page }) => {
  // 1) Panel açılıyor.
  await page.goto("/");
  await expect(page.getByText("Radar")).toBeVisible();
  await expect(page.getByRole("button", { name: "Tara" })).toBeVisible();

  // 2) Keşif tetikleniyor (fixture worker gerçek job çalıştırır).
  await page.getByLabel("Keşif sorgusu").fill("Samsun");
  await page.getByRole("button", { name: "Tara" }).click();

  // 3) İş bitiyor ve tablo gerçek DB ile doluyor.
  await expect(page.getByText("Tarama bitti")).toBeVisible({ timeout: 40_000 });
  await expect(page.locator("tbody tr").first()).toBeVisible();

  // 4) Bir aday satırı seçilip denetim paneli açılıyor.
  await page.locator("tbody tr").first().click();
  await expect(page.getByRole("dialog")).toBeVisible();

  // qualified bir satır seçildiyse denetim başlatılabilir; her hâlükârda panel
  // açılmış ve akış kırılmamış olmalı (smoke). qualified ise skoru da doğrula.
  const denetimDugmesi = page.getByRole("button", { name: "Derin denetim" });
  if (await denetimDugmesi.count()) {
    await denetimDugmesi.click();
    await expect(page.getByText("Görünürlük skoru")).toBeVisible({
      timeout: 40_000,
    });
  }
});
