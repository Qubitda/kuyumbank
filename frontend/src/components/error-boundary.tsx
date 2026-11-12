import React from "react";
import { Button } from "@/components/ui/button";
import { AlertCircle } from "lucide-react";

interface Props {
  children: React.ReactNode;
  label?: string;
}

interface State {
  error: Error | null;
}

/** Vite SPA hata sınırı — Next.js error.tsx yerine. */
export class AppErrorBoundary extends React.Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    if (import.meta.env.DEV) {
      console.error("[AppErrorBoundary]", error, info.componentStack);
    }
  }

  render() {
    if (!this.state.error) return this.props.children;

    return (
      <div className="flex min-h-[40vh] flex-col items-center justify-center gap-3 p-8 text-center">
        <AlertCircle className="h-8 w-8 text-destructive" />
        <h2 className="text-base font-semibold text-foreground">
          {this.props.label || "Beklenmeyen hata"}
        </h2>
        <p className="max-w-md text-xs text-muted-foreground">
          {this.state.error.message || "Sayfa yüklenirken bir hata oluştu."}
        </p>
        <Button
          size="sm"
          variant="outline"
          onClick={() => {
            this.setState({ error: null });
            window.location.assign("/");
          }}
        >
          Ana sayfaya dön
        </Button>
      </div>
    );
  }
}
