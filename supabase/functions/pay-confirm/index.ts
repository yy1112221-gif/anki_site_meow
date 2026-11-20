// MEOWCA! 결제 승인 — 토스 결제창에서 돌아온 paymentKey·orderId·amount를 서버 주문서와 맞춰 본 뒤 토스에 승인 요청
// 필요한 Secret: TOSS_SECRET_KEY (토스 상점관리자 > 개발 > API 키의 '시크릿 키'. 채팅에 붙이지 말고 Supabase Secrets에만)
// SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY 는 Supabase가 서버 안에서 자동으로 넣어 줌
const SB = Deno.env.get("SUPABASE_URL")!, SR = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, TK = Deno.env.get("TOSS_SECRET_KEY") || "";
const ORIGINS = ["https://meowca.app", "https://www.meowca.app", "https://yy1112221-gif.github.io"];
const cors = (o: string | null) => ({ "Access-Control-Allow-Origin": o && ORIGINS.includes(o) ? o : ORIGINS[0], "Access-Control-Allow-Headers": "content-type, apikey, authorization", "Access-Control-Allow-Methods": "POST, OPTIONS", "content-type": "application/json" });
const db = (path: string, init: RequestInit = {}) => fetch(`${SB}/rest/v1/${path}`, { ...init, headers: { apikey: SR, Authorization: `Bearer ${SR}`, "content-type": "application/json", Prefer: "return=representation", ...(init.headers || {}) } });

Deno.serve(async (req) => {
  const H = cors(req.headers.get("origin"));
  if (req.method === "OPTIONS") return new Response("ok", { headers: H });
  try {
    const { paymentKey, orderId, amount } = await req.json();
    if (!paymentKey || !orderId || !Number.isFinite(+amount)) return new Response(JSON.stringify({ ok: false, code: "BAD" }), { status: 400, headers: H });
    const o = (await (await db(`pay_order?order_id=eq.${encodeURIComponent(orderId)}&select=*`)).json())[0];
    if (!o) return new Response(JSON.stringify({ ok: false, code: "NO_ORDER" }), { status: 404, headers: H });
    if (o.status === "paid") return new Response(JSON.stringify({ ok: o.payment_key === paymentKey, item: o.item, again: true }), { headers: H });   // 새로고침 등 중복 호출
    if (+amount !== o.amount) return new Response(JSON.stringify({ ok: false, code: "AMOUNT" }), { status: 400, headers: H });
    const r = await fetch("https://api.tosspayments.com/v1/payments/confirm", { method: "POST",
      headers: { Authorization: "Basic " + btoa(TK + ":"), "content-type": "application/json", "Idempotency-Key": orderId },
      body: JSON.stringify({ paymentKey, orderId, amount: o.amount }) });
    const j = await r.json();
    if (!r.ok) return new Response(JSON.stringify({ ok: false, code: j.code, msg: j.message }), { status: 400, headers: H });
    await db(`pay_order?order_id=eq.${encodeURIComponent(orderId)}`, { method: "PATCH", body: JSON.stringify({ status: "paid", payment_key: paymentKey, paid_at: new Date().toISOString() }) });
    return new Response(JSON.stringify({ ok: true, item: o.item, receipt: j.receipt?.url || null }), { headers: H });
  } catch (e) { return new Response(JSON.stringify({ ok: false, code: "ERR" }), { status: 500, headers: H }); }
});
