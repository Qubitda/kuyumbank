"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { User, LogIn, LogOut, ShieldCheck } from "lucide-react";
import { ThemeToggle } from "./theme-toggle";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { MeResponse } from "@/lib/api/types";

interface HeaderProps {
  user?: MeResponse | null;
  onLogout?: () => void;
}

const ROUTE_TITLES: Record<string, string> = {
  "/": "Genel Bakış",
  "/firmalar": "Firmalar",
  "/tanimlar": "Tanımlar",
  "/urunler": "Ürünler & Katalog",
  "/fiyatlama": "Fiyatlama & Quote",
  "/stok": "Stok & Ledger",
  "/siparis": "Siparişler & Sepet",
  "/finans": "Finans & Cari",
  "/kalite": "Kalite Kontrol",
  "/lojistik": "Lojistik & Sevkiyat",
  "/belgeler": "Belgeler & Sertifikalar",
  "/login": "Kullanıcı Girişi",
};

export function Header({ user, onLogout }: HeaderProps) {
  const pathname = usePathname();
  const currentTitle = ROUTE_TITLES[pathname] || "Kuyumbank Portal";

  return (
    <header className="flex h-[56px] w-full items-center justify-between border-b border-border bg-card px-6">
      {/* Sol: Mevcut Route ve Seviye */}
      <div className="flex items-center gap-3">
        <h1 className="text-base font-semibold tracking-tight text-foreground">
          {currentTitle}
        </h1>
        <span className="font-mono text-xs text-muted-foreground border-l border-border pl-3">
          {pathname}
        </span>
      </div>

      {/* Sağ: Tema ve Kullanıcı Oturumu */}
      <div className="flex items-center gap-2">
        <ThemeToggle />

        {user ? (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="gap-2 h-9 border-border text-foreground"
              >
                <User className="h-4 w-4" />
                <span className="max-w-[120px] truncate text-xs font-medium">
                  {user.username}
                </span>
                {user.rol && (
                  <span className="font-mono text-[11px] text-muted-foreground">
                    ({user.rol})
                  </span>
                )}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1">
                  <p className="text-xs font-medium text-foreground">
                    {user.username}
                  </p>
                  <p className="text-[11px] text-muted-foreground truncate">
                    Firma: {user.firma ? user.firma.ad : "— (Platform)"}
                  </p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <Link href="/" className="cursor-pointer text-xs">
                  <ShieldCheck className="mr-2 h-3.5 w-3.5" />
                  Oturum & Yetkiler
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              {onLogout && (
                <DropdownMenuItem
                  onClick={onLogout}
                  className="cursor-pointer text-xs text-destructive focus:text-destructive"
                >
                  <LogOut className="mr-2 h-3.5 w-3.5" />
                  Güvenli Çıkış
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        ) : (
          <Button asChild variant="outline" size="sm" className="gap-2 h-9">
            <Link href="/login">
              <LogIn className="h-4 w-4" />
              <span>Giriş Yap</span>
            </Link>
          </Button>
        )}
      </div>
    </header>
  );
}
