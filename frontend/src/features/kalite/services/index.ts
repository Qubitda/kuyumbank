import { apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

export function listInspections(): Promise<
  components["schemas"]["OpsInspectionPage"]
> {
  return apiFetch("/ops/inspections/");
}

export function createInspection(
  body: components["schemas"]["OpsInspectionCreateRequest"],
  idempotencyKey: string,
): Promise<components["schemas"]["OpsInspection"]> {
  return apiFetch("/ops/inspections/", {
    method: "POST",
    body,
    idempotencyKey,
  });
}
