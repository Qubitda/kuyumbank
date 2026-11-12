import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";

createRoot(document.getElementById("root")!).render(<App />);

/**
 * SW: yalnızca production. Eski cache-first SW varsa güncelle / claim.
 * Geliştirmede kalan SW varsa bilinçli temizlenir (stale UI önleme).
 */
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    if (import.meta.env.PROD) {
      navigator.serviceWorker.register("/sw.js").catch(() => {
        // Kayıt başarısız — uygulama network ile çalışmaya devam eder.
      });
    } else {
      void navigator.serviceWorker.getRegistrations().then((regs) => {
        for (const reg of regs) void reg.unregister();
      });
      if ("caches" in window) {
        void caches.keys().then((keys) => {
          for (const key of keys) void caches.delete(key);
        });
      }
    }
  });
}
