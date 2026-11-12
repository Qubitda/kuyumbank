import { describe, expect, it } from "vitest";
import { isQuoteExpired } from "./quote-countdown";

describe("isQuoteExpired", () => {
  it("expires_at yoksa false", () => {
    expect(isQuoteExpired(null)).toBe(false);
    expect(isQuoteExpired(undefined)).toBe(false);
  });

  it("gelecek tarih false", () => {
    const future = new Date(Date.now() + 60_000).toISOString();
    expect(isQuoteExpired(future)).toBe(false);
  });

  it("geçmiş tarih true", () => {
    const past = new Date(Date.now() - 1_000).toISOString();
    expect(isQuoteExpired(past)).toBe(true);
  });
});
