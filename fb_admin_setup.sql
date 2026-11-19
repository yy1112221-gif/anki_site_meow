-- MEOWCA! 문의 자동 수집(1시간마다 Claude 예약 작업)용 관리 함수
-- 운영자 전용 암호(해시만 저장)를 아는 쪽만 문의를 읽고 상태·답장을 쓸 수 있음. service_role 키는 쓰지 않음
create table if not exists public.fb_admin (k text primary key);
alter table public.fb_admin enable row level security;
revoke all on public.fb_admin from anon, authenticated;

create or replace function public.fb_admin_ok(p_secret text) returns boolean
language sql security definer set search_path = public as $$
  select exists(select 1 from fb_admin where k = encode(sha256(convert_to(coalesce(p_secret,''), 'UTF8')), 'hex'));
$$;

-- 처리 안 된 문의 목록 (오래된 순, 최대 50)
create or replace function public.fb_admin_list(p_secret text) returns jsonb
language plpgsql security definer set search_path = public as $$
begin
  if not fb_admin_ok(p_secret) then raise exception 'denied'; end if;
  return coalesce((select jsonb_agg(to_jsonb(f) order by f.created_at) from (
    select id, created_at, kind, msg, diag, status, reply from feedback
    where status in ('new','waiting_owner') and kind not in ('solved') order by created_at limit 50) f), '[]'::jsonb);
end; $$;

-- 상태 바꾸기(+선택: 답장). 답장을 넣으면 사용자 앱에 빨간 점
create or replace function public.fb_admin_mark(p_secret text, p_id uuid, p_status text, p_reply text default null) returns void
language plpgsql security definer set search_path = public as $$
begin
  if not fb_admin_ok(p_secret) then raise exception 'denied'; end if;
  update feedback set status = p_status,
    reply = coalesce(p_reply, reply),
    replied_at = case when p_reply is not null then now() else replied_at end
  where id = p_id;
end; $$;

-- 이용자 수·문의량 (예약 간격 제안용)
create or replace function public.fb_admin_stats(p_secret text) returns jsonb
language plpgsql security definer set search_path = public as $$
begin
  if not fb_admin_ok(p_secret) then raise exception 'denied'; end if;
  return jsonb_build_object(
    'dau_24h',   (select count(distinct dev) from events where n = 'open' and at > now() - interval '24 hours'),
    'wau_7d',    (select count(distinct dev) from events where n = 'open' and at > now() - interval '7 days'),
    'new_devices_24h', (select count(*) from (select dev from events where n='open' group by dev having min(at) > now() - interval '24 hours') x),
    'fb_1h',     (select count(*) from feedback where kind not in ('auto','solved') and created_at > now() - interval '1 hour'),
    'fb_24h',    (select count(*) from feedback where kind not in ('auto','solved') and created_at > now() - interval '24 hours'),
    'auto_err_24h', (select count(*) from feedback where kind = 'auto' and created_at > now() - interval '24 hours'),
    'pending',   (select count(*) from feedback where status in ('new','waiting_owner') and kind not in ('solved')));
end; $$;

revoke all on function public.fb_admin_ok(text), public.fb_admin_list(text), public.fb_admin_mark(text, uuid, text, text), public.fb_admin_stats(text) from public;
grant execute on function public.fb_admin_list(text), public.fb_admin_mark(text, uuid, text, text), public.fb_admin_stats(text) to anon;

-- ▼ 마지막 한 줄(암호 해시 등록)은 채팅에서 받은 줄을 따로 실행
