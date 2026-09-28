export type TargetTier = "1:1" | "1:Few" | "1:Many";
export type CopyChannel = "Executive EDM" | "LinkedIn Ad" | "Landing Page Hook";
export type CopyStatus = "draft" | "approved" | "synced";
export interface Account { id: string; name: string; industry: string; target_tier: TargetTier; current_score: number; created_at?: string; }
export interface IntentEvent { id: string; account_id: string; source: string; event_type: string; weight: number; timestamp: string; }
export interface CopyVariant { id?: string; account_id?: string; channel: CopyChannel; generated_text: string; status: CopyStatus; }
export interface GenerateCopyResponse { account_id: string; variants: CopyVariant[]; }
