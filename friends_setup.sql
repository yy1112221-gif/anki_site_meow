-- MEOWCA! 친구(초대 링크·생일·학습 현황 공개) — 사업안 §7 ①
-- Supabase → SQL Editor → New query → 전체 붙여넣기 → Run (여러 번 실행해도 안전)
-- 주인 구분은 닉네임과 같은 방식: 기기 데이터 안의 비밀키(nick.key)의 sha256 해시. 표는 직접 못 읽고 아래 함수로만.

create table if not exists public.fr_profile (
  owner       text primary key,               -- sha256(nick.key)
  nick        text not null default '',
  fur         text not null default '',
  share_stats boolean not null default false, -- 「친구에게 학습 현황 보이기」 기본 끔
  share_bday  boolean not null default false, -- 「생일 알려 주기」 기본 끔
  bday        text,                           -- 'MM-DD' (연도 없음), share_bday일 때만 저장
  stats       jsonb,                          -- {st:연속일, wk:이번 주 학습 카드 수, lang}, share_stats일 때만 저장
  at          timestamptz not null default now()
);
create table if not exists public.fr_invite (
  token    text primary key,
  owner    text not null,
  created  timestamptz not null default now(),
  expires  timestamptz not null default now() + interval '7 days',
  used_by  text,
  used_at  timestamptz
);
create index if not exists fr_invite_owner on public.fr_invite(owner);
create table if not exists public.fr_link (
  a        text not null,                     -- a < b
  b        text not null,
  status   text not null default 'ok',        -- ok | blocked
  blocker  text,
  created  timestamptz not null default now(),
  primary key (a, b)
);
create index if not exists fr_link_b on public.fr_link(b);
alter table public.fr_profile enable row level security;
alter table public.fr_invite  enable row level security;
alter table public.fr_link    enable row level security;
revoke all on public.fr_profile, public.fr_invite, public.fr_link from anon, authenticated;

create or replace function public.fr_owner(p_key text) returns text language sql immutable as $$
  select case when p_key is null or length(p_key) < 20 then null else encode(sha256(convert_to(p_key, 'UTF8')), 'hex') end $$;

-- 내 프로필 올리기 + 친구 목록 받기. 공개를 끄면 그 값은 서버에서 바로 지움
create or replace function public.fr_sync(p_key text, p_nick text, p_fur text, p_share_stats boolean, p_share_bday boolean, p_bday text, p_stats jsonb)
returns jsonb language plpgsql security definer set search_path = public as $$
declare o text := fr_owner(p_key); bd text := nullif(btrim(coalesce(p_bday, '')), '');
begin
  if o is null then return jsonb_build_object('err', 'bad'); end if;
  if bd is not null and bd !~ '^(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$' then bd := null; end if;
  insert into fr_profile(owner, nick, fur, share_stats, share_bday, bday, stats, at)
  values (o, left(coalesce(p_nick, ''), 24), left(coalesce(p_fur, ''), 24), coalesce(p_share_stats, false), coalesce(p_share_bday, false),
          case when p_share_bday then bd end, case when p_share_stats then p_stats end, now())
  on conflict (owner) do update set nick = excluded.nick, fur = excluded.fur, share_stats = excluded.share_stats, share_bday = excluded.share_bday,
          bday = excluded.bday, stats = excluded.stats, at = now();
  return jsonb_build_object('list', coalesce((
    select jsonb_agg(jsonb_build_object('id', f.owner, 'nick', f.nick, 'fur', f.fur,
             'stats', case when f.share_stats then f.stats end, 'bday', case when f.share_bday then f.bday end, 'since', l.created) order by l.created)
    from fr_link l join fr_profile f on f.owner = case when l.a = o then l.b else l.a end
    where (l.a = o or l.b = o) and l.status = 'ok'), '[]'::jsonb));
end $$;

-- 초대 링크 만들기(7일, 1회용). 하루 30개까지
create or replace function public.fr_invite_make(p_key text) returns text
language plpgsql security definer set search_path = public as $$
declare o text := fr_owner(p_key); tk text;
begin
  if o is null then return 'bad'; end if;
  if (select count(*) from fr_invite where owner = o and created > now() - interval '1 day') >= 30 then return 'limit'; end if;
  tk := replace(gen_random_uuid()::text, '-', '');
  insert into fr_invite(token, owner) values (tk, o);
  return tk;
end $$;

-- 초대 미리 보기(수락 확인 화면용): 보낸 사람 닉네임·털만
create or replace function public.fr_invite_peek(p_token text) returns jsonb
language sql security definer set search_path = public as $$
  select coalesce((select jsonb_build_object('nick', coalesce(f.nick, ''), 'fur', coalesce(f.fur, ''),
           'st', case when i.used_by is not null then 'used' when i.expires < now() then 'expired' else 'ok' end)
    from fr_invite i left join fr_profile f on f.owner = i.owner where i.token = p_token), jsonb_build_object('st', 'none')) $$;

-- 수락: 받은 사람 프로필이 없으면 만들고 친구 맺기
create or replace function public.fr_invite_accept(p_key text, p_token text, p_nick text, p_fur text) returns text
language plpgsql security definer set search_path = public as $$
declare o text := fr_owner(p_key); i fr_invite%rowtype; x text; y text;
begin
  if o is null then return 'bad'; end if;
  select * into i from fr_invite where token = p_token for update;
  if not found then return 'none'; end if;
  if i.owner = o then return 'self'; end if;
  if i.used_by is not null then return case when i.used_by = o then 'ok' else 'used' end; end if;
  if i.expires < now() then return 'expired'; end if;
  x := least(i.owner, o); y := greatest(i.owner, o);
  if exists(select 1 from fr_link where a = x and b = y and status = 'blocked') then return 'blocked'; end if;
  insert into fr_profile(owner, nick, fur) values (o, left(coalesce(p_nick, ''), 24), left(coalesce(p_fur, ''), 24)) on conflict (owner) do nothing;
  insert into fr_link(a, b) values (x, y) on conflict (a, b) do update set status = 'ok', blocker = null;
  update fr_invite set used_by = o, used_at = now() where token = p_token;
  return 'ok';
end $$;

-- 친구 끊기(행 삭제) / 차단(다시 초대해도 안 됨)
create or replace function public.fr_remove(p_key text, p_fid text, p_block boolean) returns text
language plpgsql security definer set search_path = public as $$
declare o text := fr_owner(p_key); x text; y text;
begin
  if o is null or p_fid is null then return 'bad'; end if;
  x := least(o, p_fid); y := greatest(o, p_fid);
  if p_block then
    insert into fr_link(a, b, status, blocker) values (x, y, 'blocked', o) on conflict (a, b) do update set status = 'blocked', blocker = o;
  else
    delete from fr_link where a = x and b = y and status = 'ok';
  end if;
  return 'ok';
end $$;

-- 내 기기 데이터 지우기·탈퇴용: 내 친구 정보 전부 삭제
create or replace function public.fr_forget(p_key text) returns text
language plpgsql security definer set search_path = public as $$
declare o text := fr_owner(p_key);
begin
  if o is null then return 'bad'; end if;
  delete from fr_link where (a = o or b = o) and status = 'ok';
  delete from fr_invite where owner = o;
  delete from fr_profile where owner = o;
  return 'ok';
end $$;

-- 운영자: 사업안 §6 숫자(초대 수·수락률·친구 쌍). 운영자 비밀값 필요
create or replace function public.fr_admin_stats(p_secret text) returns jsonb
language plpgsql security definer set search_path = public as $$
begin
  if not fb_admin_ok(p_secret) then raise exception 'no'; end if;
  return jsonb_build_object(
    'profiles', (select count(*) from fr_profile),
    'inviters', (select count(distinct owner) from fr_invite),
    'invites', (select count(*) from fr_invite),
    'accepted', (select count(*) from fr_invite where used_by is not null),
    'pairs', (select count(*) from fr_link where status = 'ok'),
    'blocked', (select count(*) from fr_link where status = 'blocked'),
    'share_stats', (select count(*) from fr_profile where share_stats),
    'share_bday', (select count(*) from fr_profile where share_bday));
end $$;

revoke all on function public.fr_sync(text, text, text, boolean, boolean, text, jsonb), public.fr_invite_make(text), public.fr_invite_peek(text),
  public.fr_invite_accept(text, text, text, text), public.fr_remove(text, text, boolean), public.fr_forget(text), public.fr_admin_stats(text) from public;
grant execute on function public.fr_sync(text, text, text, boolean, boolean, text, jsonb), public.fr_invite_make(text), public.fr_invite_peek(text),
  public.fr_invite_accept(text, text, text, text), public.fr_remove(text, text, boolean), public.fr_forget(text), public.fr_admin_stats(text) to anon, authenticated;
