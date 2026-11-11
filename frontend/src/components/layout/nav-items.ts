import type { ComponentType } from "react";
import {
  Building2,
  Sliders,
  Gem,
  Tag,
  Boxes,
  ShoppingCart,
  Receipt,
  CheckCircle,
  Truck,
  FileText,
} from "lucide-react";
import type { Capabilities } from "@/lib/api/types";

export interface NavItem {
  href: string;
  label: string;
  backendApp: string;
  icon: ComponentType<{ className?: string }>;
  requiredCapability?: keyof Capabilities;
}

export const DOMAIN_NAV_ITEMS: NavItem[] = [
  {
    href: "/firmalar",
    label: "Firmalar",
    backendApp: "firmalar",
    icon: Building2,
    requiredCapability: "can_manage_org",
  },
  {
    href: "/tanimlar",
    label: "Tanımlar",
    backendApp: "tanimlar",
    icon: Sliders,
    requiredCapability: "can_view_ops",
  },
  {
    href: "/urunler",
    label: "Ürünler",
    backendApp: "urunler",
    icon: Gem,
    requiredCapability: "can_view_catalog",
  },
  {
    href: "/fiyatlama",
    label: "Fiyatlama",
    backendApp: "fiyatlama",
    icon: Tag,
    requiredCapability: "can_lock_quote",
  },
  {
    href: "/stok",
    label: "Stok",
    backendApp: "stok",
    icon: Boxes,
    requiredCapability: "can_view_supplier_stock",
  },
  {
    href: "/siparis",
    label: "Sipariş",
    backendApp: "siparis",
    icon: ShoppingCart,
    requiredCapability: "can_view_orders",
  },
  {
    href: "/finans",
    label: "Finans",
    backendApp: "finans",
    icon: Receipt,
    requiredCapability: "can_view_finance",
  },
  {
    href: "/kalite",
    label: "Kalite",
    backendApp: "kalite",
    icon: CheckCircle,
    requiredCapability: "can_manage_qc",
  },
  {
    href: "/lojistik",
    label: "Lojistik",
    backendApp: "lojistik",
    icon: Truck,
    requiredCapability: "can_view_shipments",
  },
  {
    href: "/belgeler",
    label: "Belgeler",
    backendApp: "belgeler",
    icon: FileText,
  },
];
