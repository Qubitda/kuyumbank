"use client";

import { useEffect, useState, useTransition } from "react";

import { Button } from "@/components/ui/button";
import {
  approveRfqMatch,
  createRfqMatch,
  listRfqMatchCandidates,
  listRfqMatches,
  rejectRfqMatch,
} from "@/features/siparis/services";
import { ApiError, apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { newIdempotencyKey } from "@/lib/utils";

type Rfq = components["schemas"]["Rfq"];
type RfqPage = { results?: Rfq[]; count?: number };
type RfqLine = {
  id?: number;
  aciklama?: string;
  miktar?: string;
  birim?: string;
  varyant_id?: number | null;
};
type Candidate = {
  varyant_id: number;
  sku?: string;
  urun_ad?: string;
  platform_kodu?: string;
  skor?: number;
};
type Match = components["schemas"]["RfqMatch"];

export function AdminRfqMatchClient() {
  const [rfqs, setRfqs] = useState<Rfq[]>([]);
  const [activeRfq, setActiveRfq] = useState<Rfq | null>(null);
  const [lineId, setLineId] = useState<number | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [matches, setMatches] = useState<Match[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  useEffect(() => {
    let cancelled = false;
    apiFetch<RfqPage>("/rfqs/")
      .then((page) => {
        if (!cancelled) {
          setRfqs(page.results ?? []);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "RFQ listesi alınamadı.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  function selectRfq(rfq: Rfq) {
    setActiveRfq(rfq);
    setMessage(null);
    const lines = (rfq.lines ?? []) as RfqLine[];
    const first = lines.find((l) => l.id != null);
    setLineId(first?.id ?? null);
    setCandidates([]);
    setMatches([]);
  }

  function loadLine(id: number) {
    setLineId(id);
    setError(null);
    startTransition(async () => {
      try {
        const [cand, matchList] = await Promise.all([
          listRfqMatchCandidates(id),
          listRfqMatches(id),
        ]);
        setCandidates((cand.results ?? []) as Candidate[]);
        setMatches(matchList.results ?? []);
      } catch (err) {
        setError(
          err instanceof ApiError ? err.message : "Eşleştirme verisi alınamadı.",
        );
      }
    });
  }

  useEffect(() => {
    if (lineId != null) loadLine(lineId);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- lineId tetikler
  }, [lineId]);

  function propose(varyantId: number, skor?: number) {
    if (lineId == null) return;
    setError(null);
    setMessage(null);
    startTransition(async () => {
      try {
        await createRfqMatch(
          lineId,
          {
            varyant_id: varyantId,
            skor: skor ?? 0,
            kanit: { kaynak: "admin_ui" },
          },
          newIdempotencyKey(),
        );
        setMessage(`Öneri kaydedildi · varyant #${varyantId}`);
        loadLine(lineId);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Öneri başarısız.");
      }
    });
  }

  function approve(id: number) {
    setError(null);
    startTransition(async () => {
      try {
        await approveRfqMatch(id, newIdempotencyKey());
        setMessage(`Eşleştirme onaylandı #${id}`);
        if (lineId != null) loadLine(lineId);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Onay başarısız.");
      }
    });
  }

  function reject(id: number) {
    setError(null);
    startTransition(async () => {
      try {
        await rejectRfqMatch(id, "admin red", newIdempotencyKey());
        setMessage(`Eşleştirme reddedildi #${id}`);
        if (lineId != null) loadLine(lineId);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Red başarısız.");
      }
    });
  }

  const lines = (activeRfq?.lines ?? []) as RfqLine[];

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold tracking-tight">RFQ eşleştirme</h1>
        <p className="text-sm text-muted-foreground">
          Tedarikçiye yönlendirme: aday varyant öner → onay. Alıcıya fiyat
          quote/sepet akışıyla gider (kör havuz).
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

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-medium">Gelen RFQ</h2>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[28rem] border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-left text-muted-foreground">
                <th className="py-2 pr-3 font-medium">ID</th>
                <th className="py-2 pr-3 font-medium">Durum</th>
                <th className="py-2 pr-3 font-medium">Tip</th>
                <th className="py-2 font-medium"> </th>
              </tr>
            </thead>
            <tbody>
              {rfqs.map((r) => (
                <tr key={r.id} className="border-b border-border">
                  <td className="py-2 pr-3 font-mono text-xs">#{r.id}</td>
                  <td className="py-2 pr-3">{r.durum}</td>
                  <td className="py-2 pr-3">{r.talep_tipi || "—"}</td>
                  <td className="py-2">
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => selectRfq(r)}
                    >
                      Seç
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {rfqs.length === 0 ? (
          <p className="text-sm text-muted-foreground">RFQ yok.</p>
        ) : null}
      </section>

      {activeRfq ? (
        <section className="flex flex-col gap-4 border-t border-border pt-6">
          <h2 className="text-sm font-medium">
            RFQ #{activeRfq.id} satırları
          </h2>
          <div className="flex flex-wrap gap-2">
            {lines.map((l) =>
              l.id == null ? null : (
                <Button
                  key={l.id}
                  type="button"
                  size="sm"
                  variant={lineId === l.id ? "default" : "outline"}
                  onClick={() => setLineId(l.id!)}
                >
                  #{l.id} · {l.miktar || "?"} {l.birim || ""}
                </Button>
              ),
            )}
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <div className="flex flex-col gap-2">
              <h3 className="text-xs uppercase tracking-wide text-muted-foreground">
                Adaylar
              </h3>
              {pending && candidates.length === 0 ? (
                <p className="text-sm text-muted-foreground">Yükleniyor…</p>
              ) : null}
              <ul className="flex flex-col gap-2">
                {candidates.map((c) => (
                  <li
                    key={c.varyant_id}
                    className="flex items-center justify-between gap-2 border-b border-border py-2 text-sm"
                  >
                    <span>
                      {c.urun_ad || "Ürün"} ·{" "}
                      <span className="font-mono text-xs">{c.sku}</span>
                      {c.skor != null ? (
                        <span className="ml-2 tabular-nums text-muted-foreground">
                          skor {c.skor}
                        </span>
                      ) : null}
                    </span>
                    <Button
                      type="button"
                      size="sm"
                      disabled={pending}
                      onClick={() => propose(c.varyant_id, c.skor)}
                    >
                      Öner
                    </Button>
                  </li>
                ))}
              </ul>
              {candidates.length === 0 ? (
                <p className="text-sm text-muted-foreground">Aday yok.</p>
              ) : null}
            </div>

            <div className="flex flex-col gap-2">
              <h3 className="text-xs uppercase tracking-wide text-muted-foreground">
                Öneriler
              </h3>
              <ul className="flex flex-col gap-2">
                {matches.map((m) => (
                  <li
                    key={m.id}
                    className="flex items-center justify-between gap-2 border-b border-border py-2 text-sm"
                  >
                    <span>
                      #{m.id} · varyant {m.varyant_id} · {m.durum}
                    </span>
                    <span className="flex gap-2">
                      <Button
                        type="button"
                        size="sm"
                        disabled={pending}
                        onClick={() => approve(m.id)}
                      >
                        Onay
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        disabled={pending}
                        onClick={() => reject(m.id)}
                      >
                        Red
                      </Button>
                    </span>
                  </li>
                ))}
              </ul>
              {matches.length === 0 ? (
                <p className="text-sm text-muted-foreground">Öneri yok.</p>
              ) : null}
            </div>
          </div>
        </section>
      ) : null}
    </div>
  );
}
