import { apiFetch, newIdempotencyKey } from "@/lib/api/client";
import type { Paginated } from "@/lib/api/types";
import type {
  BuyerReturn,
  BuyerReturnPage,
  BuyerShipment,
  DispatchShipmentRequest,
  OpsShipment,
  OpsShipmentPage,
  PodRequest,
  ShipmentCreateRequest,
} from "../types";

export const lojistikService = {
  getShipments(): Promise<OpsShipmentPage> {
    return apiFetch<OpsShipmentPage>("/ops/shipments/");
  },
  getBuyerShipments(
    params?: Record<string, string>
  ): Promise<Paginated<BuyerShipment>> {
    const query = params ? `?${new URLSearchParams(params).toString()}` : "";
    return apiFetch(`/shipments/${query}`);
  },
  createShipment(data: ShipmentCreateRequest): Promise<OpsShipment> {
    return apiFetch<OpsShipment>("/ops/shipments/", {
      method: "POST",
      body: data,
      idempotencyKey: newIdempotencyKey(),
    });
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
  cancelShipment(id: number | string): Promise<OpsShipment> {
    return apiFetch<OpsShipment>(`/ops/shipments/${id}/cancel/`, {
      method: "POST",
      idempotencyKey: newIdempotencyKey(),
    });
  },
  submitPod(id: number | string, data: PodRequest): Promise<OpsShipment> {
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
