import { z } from "zod";

/** OpenAPI OpsMeasurementRequest — ayar/gram ayrı alan yok (GAP-F4-02). */
export const measurementSchema = z.object({
  order_line_id: z.number().int().positive("Sipariş satırı zorunlu."),
  olculen_ayar: z.string().trim().optional(),
  olculen_gram: z.string().trim().optional(),
  olculen: z.string().trim().optional(),
  override_gerekce: z.string().trim().optional(),
}).superRefine((v, ctx) => {
  const hasParts = Boolean(v.olculen_ayar || v.olculen_gram);
  const hasRaw = Boolean(v.olculen);
  if (!hasParts && !hasRaw) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "Ölçülen değer veya ayar/gram girin.",
      path: ["olculen"],
    });
  }
});

export type MeasurementInput = z.infer<typeof measurementSchema>;

/** UI alanlarını OpenAPI `olculen` string’ine birleştirir. */
export function toOpsMeasurementBody(input: MeasurementInput): {
  order_line_id: number;
  olculen: string;
  override_gerekce?: string;
} {
  const parts: string[] = [];
  if (input.olculen_ayar?.trim()) parts.push(`ayar=${input.olculen_ayar.trim()}`);
  if (input.olculen_gram?.trim()) parts.push(`gram=${input.olculen_gram.trim()}`);
  const composed = parts.length
    ? parts.join(";")
    : (input.olculen?.trim() ?? "");
  return {
    order_line_id: input.order_line_id,
    olculen: composed,
    ...(input.override_gerekce?.trim()
      ? { override_gerekce: input.override_gerekce.trim() }
      : {}),
  };
}
