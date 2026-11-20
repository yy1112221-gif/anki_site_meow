-- MEOWCA! 닉네임(중복 불가) + 운영자용 계정 조회
-- Supabase → SQL Editor → New query → 전체 붙여넣기 → Run

-- 1) 닉네임: 이름은 하나뿐(대소문자 무시), 주인은 기기 데이터 안의 비밀키 해시로 구분
create table if not exists public.nick (
  name_l   text primary key,
  name     text not null,
  owner    text not null unique,
  at       timestamptz not null default now()
);
alter table public.nick enable row level security;
revoke all on public.nick from anon, authenticated;

create or replace function public.nick_claim(p_key text, p_name text) returns text
language plpgsql security definer set search_path = public as $$
declare o text; n text := btrim(coalesce(p_name, '')); nl text;
begin
  if p_key is null or length(p_key) < 20 then return 'bad'; end if;
  if n !~ '^[0-9A-Za-z_가-힣ぁ-んァ-ヶー一-龥]{2,12}$' then return 'bad'; end if;
  if n ~* '(admin|운영자|관리자|meowca|묘카|암기냥이|ミョウカ)' then return 'bad'; end if;
  o  := encode(sha256(convert_to(p_key, 'UTF8')), 'hex');
  nl := lower(n);
  if exists(select 1 from nick where name_l = nl and owner <> o) then return 'taken'; end if;
  delete from nick where owner = o and name_l <> nl;
  insert into nick(name_l, name, owner) values (nl, n, o)
    on conflict (name_l) do update set name = excluded.name, at = now();
  return 'ok';
exception when unique_violation then return 'taken';
end $$;
revoke all on function public.nick_claim(text, text) from public;
grant execute on function public.nick_claim(text, text) to anon, authenticated;

-- 2) 운영자용: 로그인 계정 수·공급자별·최근 로그인(이메일은 가려서). 운영자 비밀값 있어야만 실행
create or replace function public.fb_admin_users(p_secret text) returns jsonb
language plpgsql security definer set search_path = public, auth as $$
begin
  if not fb_admin_ok(p_secret) then raise exception 'no'; end if;
  return jsonb_build_object(
    'total', (select count(*) from auth.users),
    'by_provider', (select coalesce(jsonb_object_agg(pv, c), '{}'::jsonb) from (select coalesce(raw_app_meta_data->>'provider', '?') pv, count(*) c from auth.users group by 1) x),
    'linked', (select count(*) from public.user_link),
    'nicks', (select count(*) from public.nick),
    'recent', (select coalesce(jsonb_agg(r order by r->>'last' desc), '[]'::jsonb) from (
       select jsonb_build_object('mail', regexp_replace(coalesce(email, ''), '^(.).*(@.*)$', '\1***\2'), 'prov', raw_app_meta_data->>'provider',
         'created', created_at, 'last', last_sign_in_at, 'linked', exists(select 1 from public.user_link l where l.user_id = u.id)) r
       from auth.users u order by last_sign_in_at desc nulls last limit 10) z));
end $$;
revoke all on function public.fb_admin_users(text) from public;
grant execute on function public.fb_admin_users(text) to anon;
