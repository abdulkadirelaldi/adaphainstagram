import { defineConfig, devices } from "@playwright/test";

/**
 * Panel smoke e2e (SEC-11-N1). Kritik tarayıcı-tıklama akışının kırılmadığını
 * doğrular; kapsamlı değil, smoke.
 *
 * Panel `E2E_BASE_URL`'de (varsayılan http://localhost:3000) ayakta olmalı ve
 * backend'e (NEXT_PUBLIC_API_URL) bağlı olmalı. Backend **fixture modunda**
 * çalışır — canlı IG/Apify/Anthropic çağrısı yok (CLAUDE.md kural 6). CI'da
 * Chromium kurulumu SEC-11 kapsamındadır.
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  reporter: [["list"]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    trace: "off",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
});
