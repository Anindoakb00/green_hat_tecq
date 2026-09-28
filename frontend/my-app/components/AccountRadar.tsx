'use client';
import { Account } from '../types';

export default function AccountRadar({ accounts, activeAccountId, onSelect }: { accounts: Account[], activeAccountId?: string, onSelect: (account: Account) => void }) {
  if (!accounts || accounts.length === 0) {
    return <div className="text-slate-400 p-4 text-center">No accounts synced. Awaiting webhook data...</div>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b border-slate-800 text-slate-400 text-sm uppercase tracking-wider">
            <th className="p-4 font-medium">Company</th>
            <th className="p-4 font-medium">Industry</th>
            <th className="p-4 font-medium">Tier</th>
            <th className="p-4 font-medium text-right">Intent Score</th>
          </tr>
        </thead>
        <tbody>
          {accounts.map((account) => {
            const isActive = account.id === activeAccountId;
            const isHot = account.current_score >= 75;

            return (
              <tr
                key={account.id}
                onClick={() => onSelect(account)}
                className={`border-b border-slate-800/50 cursor-pointer transition-colors hover:bg-slate-800/50 ${isActive ? 'bg-slate-800/80 border-l-4 border-l-emerald-500' : 'border-l-4 border-l-transparent'}`}
              >
                <td className="p-4 font-medium text-white">{account.name}</td>
                <td className="p-4 text-slate-300">{account.industry}</td>
                <td className="p-4">
                  <span className="px-2 py-1 text-xs rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                    {account.target_tier}
                  </span>
                </td>
                <td className="p-4 text-right">
                  <span className={`font-bold ${isHot ? 'text-emerald-400' : 'text-blue-400'}`}>
                    {account.current_score}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}