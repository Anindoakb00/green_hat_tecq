-- Epochs Enterprise ABM Engine production schema for Supabase.
create extension if not exists pgcrypto;
create extension if not exists vector;

create table if not exists public.accounts (
    id uuid primary key default gen_random_uuid(),
    agency_user_id uuid not null references auth.users(id) on delete cascade,
    name text not null,
    industry text not null,
    target_tier text not null check (target_tier in ('1:1', '1:Few', '1:Many')),
    current_score numeric(5, 2) not null default 0 check (current_score between 0 and 100),
    created_at timestamptz not null default now()
);

create table if not exists public.intent_events (
    id uuid primary key default gen_random_uuid(),
    account_id uuid not null references public.accounts(id) on delete cascade,
    source text not null,
    event_type text not null,
    weight numeric(8, 2) not null check (weight >= 0),
    timestamp timestamptz not null default now()
);

create table if not exists public.brand_knowledge (
    id uuid primary key default gen_random_uuid(),
    agency_user_id uuid not null references auth.users(id) on delete cascade,
    theme_name text not null,
    content text not null,
    embedding vector(384),
    created_at timestamptz not null default now()
);

create table if not exists public.copy_variants (
    id uuid primary key default gen_random_uuid(),
    account_id uuid not null references public.accounts(id) on delete cascade,
    channel text not null check (channel in ('Executive EDM', 'LinkedIn Ad', 'Landing Page Hook')),
    generated_text text not null,
    status text not null default 'draft' check (status in ('draft', 'approved', 'synced')),
    created_at timestamptz not null default now()
);

create index if not exists accounts_agency_user_idx on public.accounts (agency_user_id);
create index if not exists accounts_score_idx on public.accounts (current_score desc);
create index if not exists intent_events_account_timestamp_idx on public.intent_events (account_id, timestamp desc);
create index if not exists brand_knowledge_theme_idx on public.brand_knowledge (agency_user_id, theme_name);
create index if not exists brand_knowledge_embedding_idx on public.brand_knowledge
    using ivfflat (embedding vector_cosine_ops) with (lists = 100);
create index if not exists copy_variants_account_idx on public.copy_variants (account_id, created_at desc);

alter table public.accounts enable row level security;
alter table public.intent_events enable row level security;
alter table public.brand_knowledge enable row level security;
alter table public.copy_variants enable row level security;

create policy "agency users read own accounts" on public.accounts
    for select to authenticated using (agency_user_id = (select auth.uid()));
create policy "agency users insert own accounts" on public.accounts
    for insert to authenticated with check (agency_user_id = (select auth.uid()));
create policy "agency users update own accounts" on public.accounts
    for update to authenticated using (agency_user_id = (select auth.uid()))
    with check (agency_user_id = (select auth.uid()));
create policy "agency users delete own accounts" on public.accounts
    for delete to authenticated using (agency_user_id = (select auth.uid()));

create policy "agency users read own events" on public.intent_events
    for select to authenticated using (exists (
        select 1 from public.accounts a where a.id = intent_events.account_id
        and a.agency_user_id = (select auth.uid())
    ));
create policy "agency users insert own events" on public.intent_events
    for insert to authenticated with check (exists (
        select 1 from public.accounts a where a.id = intent_events.account_id
        and a.agency_user_id = (select auth.uid())
    ));

create policy "agency users manage own brand knowledge" on public.brand_knowledge
    for all to authenticated using (agency_user_id = (select auth.uid()))
    with check (agency_user_id = (select auth.uid()));

create policy "agency users read own variants" on public.copy_variants
    for select to authenticated using (exists (
        select 1 from public.accounts a where a.id = copy_variants.account_id
        and a.agency_user_id = (select auth.uid())
    ));
create policy "agency users create own variants" on public.copy_variants
    for insert to authenticated with check (exists (
        select 1 from public.accounts a where a.id = copy_variants.account_id
        and a.agency_user_id = (select auth.uid())
    ));
create policy "agency users update own variants" on public.copy_variants
    for update to authenticated using (exists (
        select 1 from public.accounts a where a.id = copy_variants.account_id
        and a.agency_user_id = (select auth.uid())
    )) with check (exists (
        select 1 from public.accounts a where a.id = copy_variants.account_id
        and a.agency_user_id = (select auth.uid())
    ));

create or replace function public.match_brand_knowledge_for_owner(
    query_embedding vector(384), match_theme text, owner_id uuid, match_count integer default 5
)
returns table (id uuid, theme_name text, content text, similarity real)
language sql stable security invoker
as $$
    select bk.id, bk.theme_name, bk.content,
           (1 - (bk.embedding <=> query_embedding))::real as similarity
    from public.brand_knowledge bk
    where bk.agency_user_id = owner_id
      and bk.theme_name = match_theme and bk.embedding is not null
    order by bk.embedding <=> query_embedding
    limit greatest(match_count, 1);
$$;
