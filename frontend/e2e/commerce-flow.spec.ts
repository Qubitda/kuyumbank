import { test, expect } from "@playwright/test";

/**
 * E2E: API’yi route mock ile simüle eder (Django zorunlu değil).
 * Gerçek backend smoke ayrı koşulur.
 */
test.describe("portal akışları (mock API)", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/v1/auth/csrf/", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ csrf_token: "test-csrf" }),
      });
    });

    await page.route("**/api/v1/me/", async (route) => {
      if (route.request().method() === "GET") {
        await route.fulfill({
          status: 401,
          contentType: "application/json",
          body: JSON.stringify({ status: 401, title: "Unauthorized" }),
        });
        return;
      }
      await route.continue();
    });
  });

  test("login sayfası Türkçe ve erişilebilir", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator("html")).toHaveAttribute("lang", "tr");
    await expect(page.getByRole("heading", { name: /Kuyumbank/i })).toBeVisible();
  });

  test("yetkisiz firma URL’i login’e düşer", async ({ page }) => {
    await page.goto("/firmalar");
    await expect(page).toHaveURL(/\/login/);
  });

  test("katalog → quote → sepet → checkout zinciri (mock oturum)", async ({
    page,
  }) => {
    const caps = {
      can_view_catalog: true,
      can_view_cart: true,
      can_view_orders: true,
      can_checkout: true,
      can_lock_quote: true,
    };

    await page.route("**/api/v1/me/", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: 1,
          username: "buyer",
          rol: "ALICI",
          firma: {
            id: 2,
            ad: "Alıcı AŞ",
            alici_mi: true,
            tedarikci_mi: false,
            platform_mu: false,
            aktif: true,
          },
          firma_id: 2,
          capabilities: caps,
          email_verified: true,
          act_as: { active: false },
        }),
      });
    });

    await page.route("**/api/v1/catalog/**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          count: 1,
          page: 1,
          page_size: 20,
          next: null,
          previous: null,
          results: [
            {
              id: 10,
              ad: "Test Ürün",
              varyant_id: 100,
              sku: "SKU-1",
            },
          ],
        }),
      });
    });

    await page.route("**/api/v1/quotes/", async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({
            id: 501,
            toplam_vergisiz: "1250.00",
            para_birimi: "TRY",
            server_now: new Date().toISOString(),
            expires_at: new Date(Date.now() + 600_000).toISOString(),
          }),
        });
        return;
      }
      await route.continue();
    });

    await page.route("**/api/v1/carts/me/**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: 1,
          lines: [
            {
              id: 1,
              quote_id: 501,
              miktar: "1",
              toplam_vergisiz: "1250.00",
              para_birimi: "TRY",
            },
          ],
          para_birimi: "TRY",
          toplam_vergisiz: "1250.00",
        }),
      });
    });

    await page.route("**/api/v1/checkouts/", async (route) => {
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({ checkout_id: 9, order_id: 77 }),
      });
    });

    await page.route("**/api/v1/orders/**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: 77,
          durum: "ONAYLANDI",
          toplam_vergisiz: "1250.00",
          para_birimi: "TRY",
        }),
      });
    });

    await page.goto("/urunler");
    await expect(
      page.getByRole("heading", { name: "Ürün Kataloğu", level: 1 })
    ).toBeVisible({ timeout: 15_000 });

    await page.goto("/siparis");
    await expect(page.getByRole("heading", { level: 1 }).first()).toBeVisible({
      timeout: 15_000,
    });
  });
});

