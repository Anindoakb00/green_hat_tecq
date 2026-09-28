/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";
import { useState } from "react";
import type { CopyVariant, GenerateCopyResponse } from "../types";
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function CopyStudio({ activeAccount }: { activeAccount: any }) {
  const [theme, setTheme] = useState("green_hat_1.pdf");
  const [variants, setVariants] = useState<CopyVariant[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  if (!activeAccount) return null;

  async function generate() {
    setLoading(true);
    setMessage("");
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 120000);
    try {
      const response = await fetch(`${API}/api/generate-copy`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer local-demo-token` },
        body: JSON.stringify({ account_id: activeAccount.id, theme_name: theme }),
        signal: controller.signal
      });
      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || "Generation failed");
      }
      const data = (await response.json()) as GenerateCopyResponse;
      setVariants(data.variants);
    } catch (error) {
      setMessage(error instanceof DOMException && error.name === "AbortError" ? "Generation timed out. Check the backend terminal for the error." : error instanceof Error ? error.message : "Generation failed");
    } finally {
      window.clearTimeout(timeout);
      setLoading(false);
    }
  }

  async function update(id: string, status: "approved" | "synced") {
    const response = await fetch(`${API}/api/copy-variants/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Authorization: `Bearer local-demo-token` },
      body: JSON.stringify({ status })
    });
    if (response.ok) setMessage(`Variant ${status}.`);
  }

  return (
    <div className="p-5">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-semibold text-white">Execution studio</p>
          <p className="mt-1 text-xs text-slate-500">Generate grounded creative for {activeAccount.name}</p>
        </div>
        <div className="flex gap-2">
          <input value={theme} onChange={(event) => setTheme(event.target.value)} className="w-56 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-slate-200 outline-none focus:border-emerald-400" />
          <button onClick={generate} disabled={loading} className="rounded-lg bg-emerald-400 px-3 py-2 text-xs font-semibold text-slate-950 disabled:opacity-50">{loading ? "Running..." : "Trigger Epochs Engine"}</button>
        </div>
      </div>
      {message && <p className="mt-3 break-words text-xs text-amber-300">{message}</p>}
      <div className="mt-5 grid gap-3 md:grid-cols-3">
        {variants.map((variant) => (
          <article key={`${variant.channel}-${variant.generated_text.slice(0, 12)}`} className="rounded-lg border border-slate-800 bg-slate-950/40 p-4">
            <div className="flex justify-between">
              <p className="text-[10px] uppercase tracking-wider text-emerald-400">{variant.channel}</p>
              <span className="text-[10px] text-slate-500">{variant.status}</span>
            </div>
            <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-200">{variant.generated_text}</p>
            {variant.id && (
              <div className="mt-4 flex gap-2">
                <button onClick={() => update(variant.id!, "approved")} className="rounded border border-slate-700 px-2 py-1 text-[10px] text-slate-300">Approve</button>
                <button onClick={() => update(variant.id!, "synced")} className="rounded border border-emerald-400/30 px-2 py-1 text-[10px] text-emerald-300">Sync</button>
              </div>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}