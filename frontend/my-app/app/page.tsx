'use client';
import { useEffect, useState } from 'react';
import AccountRadar from '../components/AccountRadar';
import { SignalFeed } from '../components/SignalFeed';
import { CopyStudio } from '../components/CopyStudio';
import { Account, IntentEvent } from '../types';

export default function Dashboard() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [activeAccount, setActiveAccount] = useState<Account | null>(null);
  const [events, setEvents] = useState<IntentEvent[]>([]);

  // Fetch real accounts from FastAPI on load
  useEffect(() => {
    fetch('http://localhost:8000/api/accounts', {
      headers: { 'Authorization': 'Bearer local-demo-token' }
    })
      .then((res) => res.json())
      .then((data) => {
        setAccounts(data);
        if (data.length > 0) setActiveAccount(data[0]);
      })
      .catch(console.error);
  }, []);

  // Fetch real events when an account is clicked
  useEffect(() => {
    if (activeAccount) {
      fetch(`http://localhost:8000/api/accounts/${activeAccount.id}/events`, {
        headers: { 'Authorization': 'Bearer local-demo-token' }
      })
        .then((res) => res.json())
        .then((data) => setEvents(data))
        .catch(console.error);
    }
  }, [activeAccount]);

  const highIntentCount = accounts.filter(a => a.current_score >= 75).length;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <header className="mb-8 border-b border-slate-800 pb-4 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-emerald-400">EPOCHS</h1>
          <p className="text-slate-400 text-sm tracking-widest uppercase">Green Hat ABM Execution Engine</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="h-3 w-3 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="text-sm text-slate-400">Live API Sync Operational</span>
        </div>
      </header>

      {/* TOP: Engine Telemetry */}
      <div className="grid grid-cols-3 gap-6 mb-8">
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl">
          <h3 className="text-slate-400 text-sm uppercase tracking-wider mb-2">Tracked Accounts</h3>
          <p className="text-4xl font-bold text-white">{accounts.length}</p>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl">
          <h3 className="text-slate-400 text-sm uppercase tracking-wider mb-2">High-Intent Accounts</h3>
          <p className="text-4xl font-bold text-emerald-400">{highIntentCount}</p>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl">
          <h3 className="text-slate-400 text-sm uppercase tracking-wider mb-2">Active Data Source</h3>
          <p className="text-xl font-semibold text-white mt-2">Supabase pgvector</p>
        </div>
      </div>

      {/* MIDDLE: Radar and Signals Split */}
      <div className="grid grid-cols-12 gap-6 mb-8">
        <div className="col-span-8 bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h2 className="text-xl font-semibold mb-4 text-white">Account Radar</h2>
          <AccountRadar accounts={accounts} activeAccountId={activeAccount?.id} onSelect={setActiveAccount}/>
        </div>
        <div className="col-span-4 bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h2 className="text-xl font-semibold mb-4 text-white">Signal Timeline</h2>
          {activeAccount && <SignalFeed account={activeAccount} events={events} loading={false}/>}
        </div>
      </div>

      {/* BOTTOM: Generative Studio */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h2 className="text-xl font-semibold mb-4 text-white">Execution Studio</h2>
        {activeAccount && <CopyStudio account={activeAccount} token="local-demo-token" />}
      </div>
    </div>
  );
}