import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

export default function NotFoundPage() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3 p-8 text-center">
      <p className="font-mono text-xs text-muted-foreground">404</p>
      <h1 className="text-xl font-semibold tracking-tight text-foreground">
        Sayfa bulunamadı
      </h1>
      <p className="max-w-sm text-xs text-muted-foreground">
        Bu yol tanımlı değil. Dinamik segmentler yalnızca açık route’larda çalışır.
      </p>
      <Button asChild size="sm">
        <Link to="/">Ana sayfa</Link>
      </Button>
    </div>
  );
}
