"use client";

import { useEffect, useState, useTransition } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type Invite = components["schemas"]["InviteCreated"];
type InvitePage = { results?: Invite[] };

export function AdminUsersClient() {
  const [invites, setInvites] = useState<Invite[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function reload() {
    return apiFetch<InvitePage>("/auth/invites/")
      .then((page) => {
        setInvites(page.results ?? []);
        setError(null);
      })
      .catch((err) => {
        setError(
          err instanceof ApiError ? err.message : "Davet listesi alınamadı.",
        );
      });
  }

  useEffect(() => {
    void reload();
  }, []);

  function onInvite(formData: FormData) {
    const email = String(formData.get("email") || "").trim();
    const rol = String(formData.get("rol") || "").trim();
    if (!email || !rol) {
      setError("email ve rol zorunlu.");
      return;
    }
    setError(null);
    setMessage(null);
    startTransition(async () => {
      try {
        const created = await apiFetch<Invite>("/auth/invites/create/", {
          method: "POST",
          body: { email, rol },
        });
        setMessage(`Davet #${created.id} · ${created.email}`);
        await reload();
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Davet başarısız.");
      }
    });
  }

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold tracking-tight">Kullanıcılar</h1>
        <p className="text-sm text-muted-foreground">
          Davet API · ürün CRUD için Django Admin (BACKEND_MAP §6.2).
        </p>
      </header>

      {error ? (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      ) : null}
      {message ? (
        <p className="text-sm text-foreground" role="status">
          {message}
        </p>
      ) : null}

      <form action={onInvite} className="grid max-w-md gap-3">
        <div className="flex flex-col gap-1">
          <Label htmlFor="email">E-posta</Label>
          <Input id="email" name="email" type="email" required />
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor="rol">Rol kodu</Label>
          <Input
            id="rol"
            name="rol"
            placeholder="alici_satinalmaci"
            required
          />
        </div>
        <Button type="submit" disabled={pending}>
          Davet gönder
        </Button>
      </form>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[28rem] border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-left text-muted-foreground">
              <th className="py-2 pr-3 font-medium">ID</th>
              <th className="py-2 pr-3 font-medium">E-posta</th>
              <th className="py-2 pr-3 font-medium">Rol</th>
              <th className="py-2 font-medium">Bitiş</th>
            </tr>
          </thead>
          <tbody>
            {invites.map((i) => (
              <tr key={i.id} className="border-b border-border">
                <td className="py-2 pr-3 font-mono text-xs">#{i.id}</td>
                <td className="py-2 pr-3">{i.email}</td>
                <td className="py-2 pr-3 font-mono text-xs">{i.rol}</td>
                <td className="py-2 text-muted-foreground">
                  {i.expires_at
                    ? new Date(i.expires_at).toLocaleString("tr-TR")
                    : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
