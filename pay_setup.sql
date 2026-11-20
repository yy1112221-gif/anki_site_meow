-- MEOWCA! 카드 결제(토스페이먼츠): 가격표 + 주문서. Supabase → SQL Editor → New query → 전체 붙여넣기 → Run
-- 가격은 서버(이 표)에서만 정해짐 → 화면에서 금액을 바꿔도 결제 확인 단계에서 걸러짐

create table if not exists public.pay_price (
  item text primary key, amount int not null check (amount > 0), name text not null);
insert into public.pay_price(item, amount, name) values
  ('snk_s', 990, '간식 한 줌'), ('snk_whale', 1500, '고래 한 마리'), ('snk_m', 2900, '간식 한 봉지'), ('snk_l', 6900, '간식 트럭'),
  ('mochi_st', 1900, '딸기 찹쌀떡 스킨'), ('mochi_mc', 1900, '말차 찹쌀떡 스킨'), ('cheese', 1900, '치즈 냥 스킨'),
  ('pudding', 1900, '푸딩 말랑 스킨'), ('sesame', 1900, '흑임자 떡 스킨'), ('soda', 2900, '소다 젤리 스킨'),
  ('s1', 500, '후원: 츄르 한 개'), ('s2', 1000, '후원: 츄르 한 봉지'), ('s3', 3000, '후원: 츄르 한 박스'), ('s4', 10000, '후원: 큰손 집사')
on conflict (item) do update set amount = excluded.amount, name = excluded.name;

create table if not exists public.pay_order (
  order_id text primary key, item text not null references public.pay_price(item), amount int not null,
  status text not null default 'ready', payment_key text, created_at timestamptz not null default now(), paid_at timestamptz);
alter table public.pay_price enable row level security; alter table public.pay_order enable row level security;
revoke all on public.pay_price, public.pay_order from anon, authenticated;

-- 주문서 만들기: 상품 id만 받아서 서버 가격으로 주문번호 발급
create or replace function public.pay_order_create(p_item text) returns jsonb
language plpgsql security definer set search_path = public as $$
declare pr record; oid text;
begin
  select * into pr from pay_price where item = p_item; if not found then raise exception 'no item'; end if;
  oid := 'mc_' || to_char(now(), 'YYMMDD') || '_' || substr(md5(random()::text || clock_timestamp()::text), 1, 16);
  insert into pay_order(order_id, item, amount) values (oid, p_item, pr.amount);
  return jsonb_build_object('orderId', oid, 'amount', pr.amount, 'orderName', pr.name);
end $$;
revoke all on function public.pay_order_create(text) from public;
grant execute on function public.pay_order_create(text) to anon, authenticated;

-- 운영자용: 최근 결제 보기 (운영자 비밀값 필요)
create or replace function public.fb_admin_pays(p_secret text) returns jsonb
language plpgsql security definer set search_path = public as $$
begin
  if not fb_admin_ok(p_secret) then raise exception 'no'; end if;
  return coalesce((select jsonb_agg(to_jsonb(o) order by o.created_at desc) from (select order_id, item, amount, status, created_at, paid_at from pay_order where status <> 'ready' order by created_at desc limit 50) o), '[]'::jsonb);
end $$;
revoke all on function public.fb_admin_pays(text) from public; grant execute on function public.fb_admin_pays(text) to anon;
