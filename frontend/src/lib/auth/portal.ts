import type { MeResponse } from "@/lib/api/types";

export type PortalKind = "buyer" | "supplier" | "admin";

/** BACKEND_MAP §7 — makul portal kökü. */
export function resolvePortal(me: MeResponse): PortalKind {
  const firma = me.firma;
  if (firma?.platform_mu || me.capabilities.can_view_ops) {
    return "admin";
  }
  if (firma?.tedarikci_mi && !firma.alici_mi) {
    return "supplier";
  }
  if (firma?.alici_mi) {
    return "buyer";
  }
  if (firma?.tedarikci_mi) {
    return "supplier";
  }
  return "buyer";
}

export function portalHome(kind: PortalKind): string {
  switch (kind) {
    case "admin":
      return "/admin";
    case "supplier":
      return "/supplier";
    default:
      return "/buyer";
  }
}

export function portalHomeForMe(me: MeResponse): string {
  return portalHome(resolvePortal(me));
}
