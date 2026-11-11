import { apiFetch } from "@/lib/api/client";
import type { OpsInspection, OpsInspectionPage, InspectionMeasurementRequest } from "../types";

export const kaliteService = {
  getInspections(): Promise<OpsInspectionPage> {
    return apiFetch<OpsInspectionPage>("/ops/inspections/");
  },
  getInspectionDetail(id: number | string): Promise<OpsInspection> {
    return apiFetch<OpsInspection>(`/ops/inspections/${id}/`);
  },
  startInspection(id: number | string): Promise<OpsInspection> {
    return apiFetch<OpsInspection>(`/ops/inspections/${id}/start/`, {
      method: "POST",
      idempotencyKey: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    });
  },
  addMeasurement(id: number | string, data: InspectionMeasurementRequest): Promise<OpsInspection> {
    return apiFetch<OpsInspection>(`/ops/inspections/${id}/measurements/`, {
      method: "POST",
      body: data,
      idempotencyKey: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    });
  },
  passInspection(id: number | string): Promise<OpsInspection> {
    return apiFetch<OpsInspection>(`/ops/inspections/${id}/pass/`, {
      method: "POST",
      idempotencyKey: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    });
  },
  failInspection(id: number | string): Promise<OpsInspection> {
    return apiFetch<OpsInspection>(`/ops/inspections/${id}/fail/`, {
      method: "POST",
      idempotencyKey: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    });
  },
};
