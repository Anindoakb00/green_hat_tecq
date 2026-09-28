/* eslint-disable @typescript-eslint/no-explicit-any */
import type { IntentEvent } from "../types";
export default function SignalFeed({ accountName, events }: { accountName?: string; events: any[] }) {
  return (
    <div className="p-5">
      <p className="text-sm font-semibold text-white">Signal timeline</p>
      <p className="mt-1 text-xs text-slate-500">Live activity for {accountName || 'Unknown'}</p>
      <div className="mt-5 space-y-4">
        {!events || events.length === 0 ? (
          <p className="text-xs text-slate-600">No intent events recorded yet.</p>
        ) : (
          events.map((event) => (
            <div key={event.id} className="border-l border-emerald-400/30 pl-3">
              <div className="flex justify-between gap-3">
                <p className="text-xs font-medium text-slate-200">{event.event_type}</p>
                <span className="text-[10px] text-slate-600">{new Date(event.timestamp).toLocaleString()}</span>
              </div>
              <p className="mt-1 text-xs text-slate-500">{event.source} · +{event.weight} points</p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}