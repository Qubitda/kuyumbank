"use client";

import { Outlet } from "react-router-dom";
import ForbiddenPage from "@/app/forbidden";
import { DomainLoading } from "@/components/route-states";
import type { Capabilities } from "@/lib/api/types";
import { useAuthContext } from "./auth-provider";

export interface RequireCapabilityProps {
  capability?: keyof Capabilities;
  anyOf?: (keyof Capabilities)[];
  children?: React.ReactNode;
}

function hasAccess(
  caps: Capabilities | null | undefined,
  capability?: keyof Capabilities,
  anyOf?: (keyof Capabilities)[]
): boolean {
  if (!capability && (!anyOf || anyOf.length === 0)) return true;
  if (!caps) return false;
  if (capability && Boolean(caps[capability])) return true;
  if (anyOf?.some((k) => Boolean(caps[k]))) return true;
  return false;
}

/**
 * Menü gizleme ≠ güvenlik. URL erişimini keser; asıl yetki backend’de.
 */
export function RequireCapability({
  capability,
  anyOf,
  children,
}: RequireCapabilityProps) {
  const { user, loading } = useAuthContext();

  if (loading) {
    return <DomainLoading label="Yetki" />;
  }

  if (!hasAccess(user?.capabilities, capability, anyOf)) {
    const needed = capability
      ? String(capability)
      : (anyOf || []).map(String).join(" | ");
    return <ForbiddenPage capability={needed} />;
  }

  if (children) return <>{children}</>;
  return <Outlet />;
}
