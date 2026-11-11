import type { Capabilities } from "@/lib/api/types";

import type { PortalKind } from "./portal";

export type NavItem = {
  href: string;
  label: string;
  /** Yoksa herkese (oturumlu) göster. */
  cap?: keyof Capabilities;
};

const BUYER_NAV: NavItem[] = [
  { href: "/buyer", label: "Özet" },
  { href: "/buyer/catalog", label: "Katalog", cap: "can_view_catalog" },
  { href: "/buyer/cart", label: "Sepet", cap: "can_view_cart" },
  { href: "/buyer/orders", label: "Siparişler", cap: "can_view_orders" },
  { href: "/buyer/rfqs", label: "Teklif talepleri", cap: "can_manage_rfq" },
  { href: "/buyer/finance", label: "Finans", cap: "can_view_finance" },
];

const SUPPLIER_NAV: NavItem[] = [
  { href: "/supplier", label: "Özet" },
  { href: "/supplier/offers", label: "Teklifler", cap: "can_manage_offers" },
  { href: "/supplier/stock", label: "Stok", cap: "can_view_supplier_stock" },
  { href: "/supplier/rfqs", label: "RFQ", cap: "can_manage_rfq" },
];

const ADMIN_NAV: NavItem[] = [
  { href: "/admin", label: "Özet" },
  { href: "/admin/orders", label: "Siparişler", cap: "can_view_orders" },
  { href: "/admin/rfq-match", label: "RFQ eşleştirme", cap: "can_view_ops" },
  { href: "/admin/qc", label: "Kalite", cap: "can_manage_qc" },
  { href: "/admin/shipments", label: "Sevkiyat", cap: "can_manage_shipment" },
  { href: "/admin/finance", label: "Finans ops", cap: "can_view_ops_finance" },
  { href: "/admin/offers", label: "Tedarikçi teklifleri", cap: "can_view_ops" },
  { href: "/admin/users", label: "Kullanıcılar", cap: "can_manage_users" },
];

export function navForPortal(kind: PortalKind): NavItem[] {
  switch (kind) {
    case "admin":
      return ADMIN_NAV;
    case "supplier":
      return SUPPLIER_NAV;
    default:
      return BUYER_NAV;
  }
}

export function filterNav(
  items: NavItem[],
  caps: Capabilities,
): NavItem[] {
  return items.filter((item) => (item.cap ? caps[item.cap] === true : true));
}
