-- MEOWCA! 로그인(기록 지키기): 계정 ↔ 동기화 코드 연결표. 본인만 읽고 쓸 수 있음
create table if not exists public.user_link (
  user_id uuid primary key references auth.users(id) on delete cascade,
  sync_code text not null,
  updated_at timestamptz not null default now()
);
alter table public.user_link enable row level security;
drop policy if exists "own row read" on public.user_link;
drop policy if exists "own row insert" on public.user_link;
drop policy if exists "own row update" on public.user_link;
create policy "own row read"   on public.user_link for select to authenticated using (auth.uid() = user_id);
create policy "own row insert" on public.user_link for insert to authenticated with check (auth.uid() = user_id);
create policy "own row update" on public.user_link for update to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);
revoke all on public.user_link from anon;
grant select, insert, update on public.user_link to authenticated;
