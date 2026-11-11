import { apiFetch } from "@/lib/api/client";
import type { OpsShipment, OpsShipmentPage, BuyerReturnPage, BuyerReturn, DispatchShipmentRequest } from "../types";

export const lojistikService = {
  getShipments(): Promise<OpsShipmentPage> {
    return apiFetch<OpsShipmentPage>("/ops/shipments/");
  },
  prepareShipment(id: number | string): Promise<OpsShipment> {
    return apiFetch<OpsShipment>(`/ops/shipments/${id}/prepare/`, {
      method: "POST",
      idempotencyKey: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    });
  },
  dispatchShipment(id: number | string, data: DispatchShipmentRequest): Promise<OpsShipment> {
    return apiFetch<OpsShipment>(`/ops/shipments/${id}/dispatch/`, {
      method: "POST",
      body: data,
      idempotencyKey: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    });
  },
  deliverShipment(id: number | string): Promise<OpsShipment> {
    return apiFetch<OpsShipment>(`/ops/shipments/${id}/deliver/`, {
      method: "POST",
      idempotencyKey: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    });
  },
  getReturns(): Promise<BuyerReturnPage> {
    return apiFetch<BuyerReturnPage>("/returns/");
  },
  approveReturn(id: number | string): Promise<BuyerReturn> {
    return apiFetch<BuyerReturn>(`/returns/${id}/approve/`, {
      method: "POST",
      idempotencyKey: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    });
  },
  mahsupReturn(id: number | string): Promise<BuyerReturn> {
    return apiFetch<BuyerReturn>(`/returns/${id}/mahsup/`, {
      method: "POST",
      idempotencyKey: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    });
  },
};
