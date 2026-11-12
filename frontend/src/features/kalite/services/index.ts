import { apiFetch, newIdempotencyKey } from "@/lib/api/client";
import type {
  InspectionCreateRequest,
  InspectionMeasurementRequest,
  OpsInspection,
  OpsInspectionPage,
} from "../types";

export const kaliteService = {
  getInspections(): Promise<OpsInspectionPage> {
    return apiFetch<OpsInspectionPage>("/ops/inspections/");
  },
  getInspectionDetail(id: number | string): Promise<OpsInspection> {
    return apiFetch<OpsInspection>(`/ops/inspections/${id}/`);
  },
  createInspection(data: InspectionCreateRequest): Promise<OpsInspection> {
    return apiFetch<OpsInspection>("/ops/inspections/", {
      method: "POST",
      body: data,
      idempotencyKey: newIdempotencyKey(),
    });
  },
  startInspection(id: number | string): Promise<OpsInspection> {
    return apiFetch<OpsInspection>(`/ops/inspections/${id}/start/`, {
      method: "POST",
      idempotencyKey: newIdempotencyKey(),
    });
  },
  addMeasurement(
    id: number | string,
    data: InspectionMeasurementRequest
  ): Promise<OpsInspection> {
    return apiFetch<OpsInspection>(`/ops/inspections/${id}/measurements/`, {
      method: "POST",
      body: data,
      idempotencyKey: newIdempotencyKey(),
    });
  },
  passInspection(id: number | string): Promise<OpsInspection> {
    return apiFetch<OpsInspection>(`/ops/inspections/${id}/pass/`, {
      method: "POST",
      idempotencyKey: newIdempotencyKey(),
    });
  },
  failInspection(id: number | string): Promise<OpsInspection> {
    return apiFetch<OpsInspection>(`/ops/inspections/${id}/fail/`, {
      method: "POST",
      idempotencyKey: newIdempotencyKey(),
    });
  },
  cancelInspection(id: number | string): Promise<OpsInspection> {
    return apiFetch<OpsInspection>(`/ops/inspections/${id}/cancel/`, {
      method: "POST",
      idempotencyKey: newIdempotencyKey(),
    });
  },
};
