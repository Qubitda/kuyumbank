import { useToast } from "@/components/ui/toast";

/**
 * Feature mutasyonlarında ortak başarı/hata toast’ı.
 * Satır içi mesaj kalabilir; toast ek yüzeydir.
 */
export function useActionToast() {
  const toast = useToast();

  return {
    success: (title: string, description?: string) =>
      toast.success(title, description),
    info: (title: string, description?: string) =>
      toast.info(title, description),
    error: (title: string, err: unknown) =>
      toast.error(
        title,
        err instanceof Error ? err.message : "İşlem tamamlanamadı."
      ),
  };
}
