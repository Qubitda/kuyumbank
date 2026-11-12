import { describe, expect, it } from "vitest";
import { ApiError } from "./client";
import { mapCommerceError } from "./commerce-errors";

describe("mapCommerceError", () => {
  it("stok mesajını eşler", () => {
    const err = new ApiError({
      status: 409,
      title: "Conflict",
      detail: "Yetersiz stok",
      code: "stock_insufficient",
    });
    expect(mapCommerceError(err, "x")).toMatch(/stok/i);
  });

  it("kredi mesajını eşler", () => {
    const err = new ApiError({
      status: 402,
      title: "Credit",
      detail: "Kredi limiti aşıldı",
      code: "credit_limit",
    });
    expect(mapCommerceError(err, "x")).toMatch(/kredi/i);
  });

  it("quote süresi mesajını eşler", () => {
    const err = new ApiError({
      status: 409,
      title: "Quote",
      detail: "Quote süresi dolmuş",
      code: "quote_expired",
    });
    expect(mapCommerceError(err, "x")).toMatch(/quote/i);
  });
});
