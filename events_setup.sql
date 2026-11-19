-- MEOWCA! 사용 기록(연구·UX 개선용). Supabase → SQL Editor 에 붙여넣고 Run (1번만)
-- 익명 기기 ID 단위. 이름·이메일·단어장 내용은 받지 않음. 항목은 p(jsonb)라 앱에서 늘려도 표를 바꿀 필요 없음
create table if not exists public.events (
  id bigint generated always as identity primary key,
  at timestamptz not null default now(),
  dev text not null,          -- 기기마다 무작위로 만든 ID
  s text,                     -- 앱을 연 한 번(세션) ID
  n text not null,            -- 이벤트 이름: open, setup, setup_done, view, ans, goal, share, preset, nerd, help_open, hide …
  p jsonb,                    -- 세부 항목
  t bigint,                   -- 기기 시각(ms)
  v text                      -- 앱 버전
);
create index if not exists events_n_at on public.events (n, at);
create index if not exists events_dev on public.events (dev);
alter table public.events enable row level security;
revoke all on public.events from anon, authenticated;

create or replace function public.ev_put(p_dev text, p_events jsonb)
returns void language plpgsql security definer set search_path = public as $$
begin
  if length(p_dev) > 64 or jsonb_typeof(p_events) <> 'array' or jsonb_array_length(p_events) > 60 or pg_column_size(p_events) > 60000 then raise exception 'bad'; end if;
  insert into events(dev, s, n, p, t, v)
  select p_dev, left(e->>'s', 16), left(e->>'n', 32), e->'p', (e->>'t')::bigint, left(e->>'v', 12) from jsonb_array_elements(p_events) e;
  delete from events where at < now() - interval '400 days';
end; $$;
revoke all on function public.ev_put(text, jsonb) from public;
grant execute on function public.ev_put(text, jsonb) to anon;

-- 보는 법 예시 (SQL Editor):
-- 첫 설정 걸린 시간(초) 중앙값:  select percentile_cont(0.5) within group (order by (p->>'ms')::int)/1000.0 from events where n='setup_done';
-- 하루 사용자 수:                select date(at), count(distinct dev) from events where n='open' group by 1 order by 1 desc;
-- 단계별 이탈:                  select p->>'step', count(distinct dev) from events where n='setup' group by 1;
