-- 集中暗記: 端末間同期用のテーブルと関数
-- Supabase の SQL Editor にこのファイルの中身を貼り付けて「Run」を押してください（1回だけ）。

create table if not exists public.vocab_sync (
  id text primary key,                 -- 同期コードの SHA-256（コードそのものは保存しない）
  data jsonb not null,
  updated_at timestamptz not null default now()
);

-- テーブルへの直接アクセスは誰にも許さない（一覧取得・総当たりを防ぐ）
alter table public.vocab_sync enable row level security;
revoke all on public.vocab_sync from anon, authenticated;

-- コードを知っている人だけが、その1件を読める
create or replace function public.sync_get(p_id text)
returns jsonb
language sql
security definer
set search_path = public
as $$
  select jsonb_build_object('data', data, 'updated_at', updated_at)
  from vocab_sync where id = p_id;
$$;

-- コードを知っている人だけが、その1件を書ける（サイズ上限 2MB）
create or replace function public.sync_put(p_id text, p_data jsonb)
returns timestamptz
language plpgsql
security definer
set search_path = public
as $$
declare t timestamptz;
begin
  if p_id !~ '^[0-9a-f]{64}$' then raise exception 'bad id'; end if;
  if pg_column_size(p_data) > 2000000 then raise exception 'too large'; end if;
  insert into vocab_sync(id, data, updated_at) values (p_id, p_data, now())
  on conflict (id) do update set data = excluded.data, updated_at = now()
  returning updated_at into t;
  return t;
end;
$$;

revoke all on function public.sync_get(text) from public;
revoke all on function public.sync_put(text, jsonb) from public;
grant execute on function public.sync_get(text) to anon;
grant execute on function public.sync_put(text, jsonb) to anon;
