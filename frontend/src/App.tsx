/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { Suspense } from "react";
import { usePathname } from "next/navigation";
import { ThemeProvider } from "@/components/layout";
import { AuthProvider } from "@/features/auth";
import PortalLayout from "@/app/(portal)/layout";
import HomePage from "@/app/page";
import LoginPage from "@/app/(auth)/login/page";
import FirmalarPage from "@/app/(portal)/firmalar/page";
import TanimlarPage from "@/app/(portal)/tanimlar/page";
import UrunlerPage from "@/app/(portal)/urunler/page";
import FiyatlamaPage from "@/app/(portal)/fiyatlama/page";
import StokPage from "@/app/(portal)/stok/page";
import SiparisPage from "@/app/(portal)/siparis/page";
import FinansPage from "@/app/(portal)/finans/page";
import KalitePage from "@/app/(portal)/kalite/page";
import LojistikPage from "@/app/(portal)/lojistik/page";
import BelgelerPage from "@/app/(portal)/belgeler/page";
import ProfilPage from "@/app/(portal)/profil/page";
import TekliflerPage from "@/app/(portal)/teklifler/page";
import RaporlarPage from "@/app/(portal)/raporlar/page";
import { DomainLoading } from "@/components/route-states";

export default function App() {
  const pathname = usePathname();

  const renderContent = () => {
    switch (pathname) {
      case "/login":
        return <LoginPage />;
      case "/firmalar":
        return (
          <PortalLayout>
            <FirmalarPage />
          </PortalLayout>
        );
      case "/tanimlar":
        return (
          <PortalLayout>
            <TanimlarPage />
          </PortalLayout>
        );
      case "/urunler":
        return (
          <PortalLayout>
            <UrunlerPage />
          </PortalLayout>
        );
      case "/fiyatlama":
        return (
          <PortalLayout>
            <FiyatlamaPage />
          </PortalLayout>
        );
      case "/stok":
        return (
          <PortalLayout>
            <StokPage />
          </PortalLayout>
        );
      case "/siparis":
        return (
          <PortalLayout>
            <SiparisPage />
          </PortalLayout>
        );
      case "/finans":
        return (
          <PortalLayout>
            <FinansPage />
          </PortalLayout>
        );
      case "/kalite":
        return (
          <PortalLayout>
            <KalitePage />
          </PortalLayout>
        );
      case "/lojistik":
        return (
          <PortalLayout>
            <LojistikPage />
          </PortalLayout>
        );
      case "/belgeler":
        return (
          <PortalLayout>
            <BelgelerPage />
          </PortalLayout>
        );
      case "/profil":
        return (
          <PortalLayout>
            <ProfilPage />
          </PortalLayout>
        );
      case "/teklifler":
        return (
          <PortalLayout>
            <TekliflerPage />
          </PortalLayout>
        );
      case "/raporlar":
        return (
          <PortalLayout>
            <RaporlarPage />
          </PortalLayout>
        );
      case "/":
      default:
        return (
          <PortalLayout>
            <HomePage />
          </PortalLayout>
        );
    }
  };

  return (
    <ThemeProvider defaultTheme="light">
      <AuthProvider>
        <Suspense fallback={<DomainLoading label="Uygulama" />}>
          {renderContent()}
        </Suspense>
      </AuthProvider>
    </ThemeProvider>
  );
}
