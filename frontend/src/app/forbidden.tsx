import { Link } from "react-router-dom";
import { ShieldOff } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function ForbiddenPage({
  capability,
}: {
  capability?: string;
}) {
  return (
    <div
      className="flex min-h-[60vh] flex-col items-center justify-center gap-3 p-8 text-center"
      role="alert"
      aria-labelledby="forbidden-title"
    >
      <p className="font-mono text-xs text-muted-foreground">403</p>
      <ShieldOff className="h-8 w-8 text-muted-foreground" aria-hidden />
      <h1
        id="forbidden-title"
        className="text-xl font-semibold tracking-tight text-foreground"
      >
        Bu sayfaya yetkiniz yok
      </h1>
      <p className="max-w-sm text-xs text-muted-foreground leading-relaxed">
        {capability ? (
          <>
            Gerekli yetki:{" "}
            <span className="font-mono text-foreground">{capability}</span>.
          </>
        ) : (
          "Bu rota için yeterli capability yok."
        )}{" "}
        Menü gizleme güvenlik değildir; işlem yetkisi backend’de doğrulanır.
      </p>
      <Button asChild size="sm">
        <Link to="/">Genel bakış</Link>
      </Button>
    </div>
  );
}
