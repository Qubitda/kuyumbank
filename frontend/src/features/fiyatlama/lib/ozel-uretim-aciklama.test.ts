import { describe, expect, it } from "vitest";
import { buildOzelUretimAciklama } from "./ozel-uretim-aciklama";

describe("buildOzelUretimAciklama", () => {
  it("montür taş ayar gram kodlar", () => {
    const s = buildOzelUretimAciklama({
      monturAd: "Burma",
      monturVaryantId: 42,
      tasOzeti: "0.30 baget",
      hedefAyar: "14",
      hedefGram: "12.50",
      not: "acil",
    });
    expect(s).toContain("[OZEL_URETIM]");
    expect(s).toContain("montur_varyant_id=42");
    expect(s).toContain("tas=0.30 baget");
    expect(s).toContain("ayar=14");
    expect(s).toContain("gram=12.50");
    expect(s.length).toBeLessThanOrEqual(255);
  });
});
