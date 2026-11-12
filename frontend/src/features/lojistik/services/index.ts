import { apiFetch, newIdempotencyKey } from "@/lib/api/client";
import type { Paginated } from "@/lib/api/types";
import type {
  OpsShipment,
  OpsShipmentPage,
  BuyerReturnPage,
  BuyerReturn,
  DispatchShipmentRequest,
} from "../types";

export const lojistikService = {
  getShipments(): Promise<OpsShipmentPage> {
    return apiFetch<OpsShipmentPage>("/ops/shipments/");
  },
  getBuyerShipments(): Promise<
    Paginated<{ id: number; durum: string; order_id?: number }>
  > {
    return apiFetch("/shipments/");
  },
  prepareShipment(id: number | string): Promise<OpsShipment> {
    return apiFetch<OpsShipment>(`/ops/shipments/${id}/prepare/`, {
      method: "POST",
      idempotencyKey: newIdempotencyKey(),
    });
  },
  dispatchShipment(
    id: number | string,
    data: DispatchShipmentRequest
  ): Promise<OpsShipment> {
    return apiFetch<OpsShipment>(`/ops/shipments/${id}/dispatch/`, {
      method: "POST",
      body: data,
      idempotencyKey: newIdempotencyKey(),
    });
  },
  deliverShipment(id: number | string): Promise<OpsShipment> {
    return apiFetch<OpsShipment>(`/ops/shipments/${id}/deliver/`, {
      method: "POST",
      idempotencyKey: newIdempotencyKey(),
    });
  },
  submitPod(
    id: number | string,
    data: { teslim_alan: string; notlar?: string; belgeler_ref?: string }
  ): Promise<OpsShipment> {
    return apiFetch<OpsShipment>(`/ops/shipments/${id}/pod/`, {
      method: "POST",
      body: data,
      idempotencyKey: newIdempotencyKey(),
    });
  },
  getReturns(): Promise<BuyerReturnPage> {
    return apiFetch<BuyerReturnPage>("/returns/");
  },
  approveReturn(id: number | string): Promise<BuyerReturn> {
    return apiFetch<BuyerReturn>(`/returns/${id}/approve/`, {
      method: "POST",
      idempotencyKey: newIdempotencyKey(),
    });
  },
  mahsupReturn(id: number | string): Promise<BuyerReturn> {
    return apiFetch<BuyerReturn>(`/returns/${id}/mahsup/`, {
      method: "POST",
      idempotencyKey: newIdempotencyKey(),
    });
  },
};
