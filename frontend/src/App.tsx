import { Suspense, useEffect } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "@/components/layout";
import { AuthProvider, RequireCapability } from "@/features/auth";
import { AppErrorBoundary } from "@/components/error-boundary";
import { DomainLoading } from "@/components/route-states";
import { ToastProvider, useToast } from "@/components/ui/toast";
import { createAppQueryClient } from "@/lib/query-client";
import PortalLayout from "@/app/(portal)/layout";
import HomePage from "@/app/page";
import LoginPage from "@/app/(auth)/login/page";
import NotFoundPage from "@/app/not-found";
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

const queryClient = createAppQueryClient();

/** Oturum düşüşü / CSRF hatalarını toast ile yüzeye çıkarır. */
function GlobalFeedbackBridge() {
  const toast = useToast();

  useEffect(() => {
    const onExpired = (event: Event) => {
      const detail = (event as CustomEvent).detail as
        | { code?: string; status?: number }
        | undefined;
      if (detail?.code === "mfa_required") {
        toast.info("Doğrulama gerekli", "Oturumu tamamlamak için MFA kodunu girin.");
        return;
      }
      toast.error("Oturum sona erdi", "Yeniden giriş yapmanız gerekiyor.");
    };
    const onCsrf = (event: Event) => {
      const detail = (event as CustomEvent).detail as
        | { message?: string }
        | undefined;
      toast.error(
        "Güvenlik jetonu alınamadı",
        detail?.message || "Sayfayı yenileyip tekrar deneyin."
      );
    };
    window.addEventListener("kuyumbank:auth-expired", onExpired);
    window.addEventListener("kuyumbank:csrf-failed", onCsrf);
    return () => {
      window.removeEventListener("kuyumbank:auth-expired", onExpired);
      window.removeEventListener("kuyumbank:csrf-failed", onCsrf);
    };
  }, [toast]);

  return null;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="light">
        <ToastProvider>
          <BrowserRouter>
            <AppErrorBoundary label="Uygulama">
              <AuthProvider>
                <GlobalFeedbackBridge />
                <Suspense fallback={<DomainLoading label="Uygulama" />}>
                  <Routes>
                    <Route path="/login" element={<LoginPage />} />

                    <Route element={<PortalLayout />}>
                      <Route index element={<HomePage />} />
                      <Route path="profil" element={<ProfilPage />} />

                      <Route
                        element={
                          <RequireCapability capability="can_manage_org" />
                        }
                      >
                        <Route path="firmalar" element={<FirmalarPage />} />
                      </Route>
                      <Route
                        element={
                          <RequireCapability capability="can_view_ops" />
                        }
                      >
                        <Route path="tanimlar" element={<TanimlarPage />} />
                        <Route path="raporlar" element={<RaporlarPage />} />
                      </Route>
                      <Route
                        element={
                          <RequireCapability capability="can_view_catalog" />
                        }
                      >
                        <Route path="urunler" element={<UrunlerPage />} />
                        <Route path="urunler/:id" element={<UrunlerPage />} />
                      </Route>
                      <Route
                        element={
                          <RequireCapability capability="can_lock_quote" />
                        }
                      >
                        <Route path="fiyatlama" element={<FiyatlamaPage />} />
                      </Route>
                      <Route
                        element={
                          <RequireCapability capability="can_view_supplier_stock" />
                        }
                      >
                        <Route path="stok" element={<StokPage />} />
                      </Route>
                      <Route
                        element={
                          <RequireCapability capability="can_view_orders" />
                        }
                      >
                        <Route path="siparis" element={<SiparisPage />} />
                        <Route path="siparis/:id" element={<SiparisPage />} />
                      </Route>
                      <Route
                        element={
                          <RequireCapability capability="can_view_finance" />
                        }
                      >
                        <Route path="finans" element={<FinansPage />} />
                      </Route>
                      <Route
                        element={
                          <RequireCapability capability="can_manage_qc" />
                        }
                      >
                        <Route path="kalite" element={<KalitePage />} />
                      </Route>
                      <Route
                        element={
                          <RequireCapability capability="can_view_shipments" />
                        }
                      >
                        <Route path="lojistik" element={<LojistikPage />} />
                      </Route>
                      <Route
                        element={
                          <RequireCapability
                            anyOf={[
                              "can_view_shipments",
                              "can_view_orders",
                              "can_view_ops",
                              "can_manage_shipment",
                            ]}
                          />
                        }
                      >
                        <Route path="belgeler" element={<BelgelerPage />} />
                      </Route>
                      <Route
                        element={
                          <RequireCapability capability="can_manage_offers" />
                        }
                      >
                        <Route path="teklifler" element={<TekliflerPage />} />
                        <Route path="teklifler/:id" element={<TekliflerPage />} />
                      </Route>

                      <Route path="*" element={<NotFoundPage />} />
                    </Route>
                  </Routes>
                </Suspense>
              </AuthProvider>
            </AppErrorBoundary>
          </BrowserRouter>
        </ToastProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
