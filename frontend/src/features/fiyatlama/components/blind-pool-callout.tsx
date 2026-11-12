"use client";

import { EyeOff } from "lucide-react";

/** Kör havuz kuralı — UI hatırlatması; güvenlik backend’de. */
export function BlindPoolCallout({ role }: { role: "buyer" | "supplier" | "both" }) {
  const text =
    role === "buyer"
      ? "Alıcı yüzeyi: tedarikçi kimliği, iç maliyet ve marj kırılımı gösterilmez. Yalnız net quote (toplam / gram başı)."
      : role === "supplier"
        ? "Tedarikçi yüzeyi: alıcı firma adı ve iletişim kör havuzda gizlidir. Yalnız RFQ teknik özeti ve kendi teklifiniz."
        : "Kör havuz: alıcı↔tedarikçi kimlik ve maliyet sızıntısı yok. Asıl yetki backend’de yeniden doğrulanır.";

  return (
    <div
      className="flex items-start gap-2 rounded-[6px] border border-border bg-muted/40 px-3 py-2 text-[11px] text-muted-foreground leading-relaxed"
      role="note"
    >
      <EyeOff className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
      <p>{text}</p>
    </div>
  );
}
