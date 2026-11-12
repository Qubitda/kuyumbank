import { describe, expect, it } from "vitest";
import { measurementSchema, toOpsMeasurementBody } from "./index";

describe("QC measurement OpenAPI mapping", () => {
  it("ayar+gram → olculen string", () => {
    const parsed = measurementSchema.parse({
      order_line_id: 7,
      olculen_ayar: "14",
      olculen_gram: "12.50",
    });
    const body = toOpsMeasurementBody(parsed);
    expect(body).toEqual({
      order_line_id: 7,
      olculen: "ayar=14;gram=12.50",
    });
  });

  it("ham olculen geçer", () => {
    const body = toOpsMeasurementBody(
      measurementSchema.parse({ order_line_id: 1, olculen: "14K 12.5g" })
    );
    expect(body.olculen).toBe("14K 12.5g");
  });

  it("boş ölçüm reddeder", () => {
    expect(() =>
      measurementSchema.parse({ order_line_id: 1 })
    ).toThrow();
  });
});
