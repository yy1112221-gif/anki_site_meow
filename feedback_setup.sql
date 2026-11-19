-- 암기냥이: 문의 냥이(피드백) 테이블과 함수
-- Supabase → SQL Editor 에 통째로 붙여넣고 Run (1번만)

create table if not exists public.feedback (
  id uuid primary key,
  created_at timestamptz not null default now(),
  kind text not null,                 -- bad / lost / ime / sound / slow / idea / other / auto(자동 오류) / solved(봇으로 해결)
  msg text not null,
  diag jsonb,                         -- 버전·브라우저·최근 오류·방금 푼 문제 3개 (단어장 내용·개인정보 없음)
  level int,                          -- 0 무시 · 1 봇/하이쿠 처리 · 2 소네트 · 3 운영자(오퍼스)
  triage jsonb,                       -- 분류 결과
  reply text,                         -- 사용자에게 보일 답장
  replied_at timestamptz,
  status text not null default 'new'  -- new / auto_replied / waiting_owner / done
);
alter table public.feedback enable row level security;
revoke all on public.feedback from anon, authenticated;

-- 쓰기: 길이 제한 + 전체 폭주 방지(1분 60건)
create or replace function public.fb_put(p_id uuid, p_kind text, p_msg text, p_diag jsonb)
returns void language plpgsql security definer set search_path = public as $$
begin
  if length(coalesce(p_msg,'')) > 1000 or length(p_kind) > 20 then raise exception 'too long'; end if;
  if pg_column_size(p_diag) > 20000 then raise exception 'diag too large'; end if;
  if (select count(*) from feedback where created_at > now() - interval '1 minute') > 60 then raise exception 'busy'; end if;
  delete from feedback where created_at < now() - interval '90 days';
  insert into feedback(id, kind, msg, diag) values (p_id, p_kind, coalesce(p_msg,''), p_diag) on conflict (id) do nothing;
end; $$;

-- 읽기: 문의 번호를 아는 사람만 자기 답장 확인
create or replace function public.fb_get(p_id uuid)
returns jsonb language sql security definer set search_path = public as $$
  select jsonb_build_object('reply', reply, 'status', status) from feedback where id = p_id;
$$;

revoke all on function public.fb_put(uuid, text, text, jsonb) from public;
revoke all on function public.fb_get(uuid) from public;
grant execute on function public.fb_put(uuid, text, text, jsonb) to anon;
grant execute on function public.fb_get(uuid) to anon;
