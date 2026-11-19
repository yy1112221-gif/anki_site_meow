// 암기냥이 문의 분류기 — Database Webhook(feedback INSERT)이 호출
// 0단계 규칙(무료) → 1단계 Haiku(분류+쉬운 답) → 2단계 Sonnet(진단+답) → 3단계 운영자 텔레그램 호출(Claude Code에서 Opus로 수정)
// 필요한 Secrets: ANTHROPIC_API_KEY, TG_TOKEN, TG_CHAT, HOOK_SECRET
// SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY 는 Supabase가 서버 안에서 자동으로 넣어 줌(어디에도 복사하지 않음)
const SB = Deno.env.get("SUPABASE_URL")!, SR = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const AK = Deno.env.get("ANTHROPIC_API_KEY") || "", TG = Deno.env.get("TG_TOKEN") || "", CHAT = Deno.env.get("TG_CHAT") || "";
const APP = `암기냥이: 한국인용 JLPT 일본어 단어 간격반복 웹앱(무료, 로그인 없음, 데이터는 기기 브라우저 저장, 기기 이동은 동기화 코드).
설정 '입력 없이'=타자 없이 고르기. 소리는 기기 음성(TTS). 귀여운 냥이에게 간식 주기. 프리셋 단어 뜻은 직접 검수됨.`;

async function claude(model: string, sys: string, user: string, max = 500) {
  const r = await fetch("https://api.anthropic.com/v1/messages", { method: "POST",
    headers: { "x-api-key": AK, "anthropic-version": "2023-06-01", "content-type": "application/json" },
    body: JSON.stringify({ model, max_tokens: max, system: sys, messages: [{ role: "user", content: user }] }) });
  const j = await r.json(); const t = j?.content?.[0]?.text || "{}";
  try { return JSON.parse(t.slice(t.indexOf("{"), t.lastIndexOf("}") + 1)); } catch { return {}; }
}
async function upd(id: string, v: Record<string, unknown>) {
  await fetch(`${SB}/rest/v1/feedback?id=eq.${id}`, { method: "PATCH",
    headers: { apikey: SR, Authorization: `Bearer ${SR}`, "content-type": "application/json" }, body: JSON.stringify(v) });
}
async function tg(text: string) {
  if (!TG || !CHAT) return;
  await fetch(`https://api.telegram.org/bot${TG}/sendMessage`, { method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ chat_id: CHAT, text: text.slice(0, 3900) }) });
}
async function recentAutoSame(msg: string) {
  const since = new Date(Date.now() - 6 * 3600e3).toISOString();
  const r = await fetch(`${SB}/rest/v1/feedback?select=id&kind=eq.auto&created_at=gte.${since}&msg=eq.${encodeURIComponent(msg)}`,
    { headers: { apikey: SR, Authorization: `Bearer ${SR}` } });
  return ((await r.json()) || []).length;
}

Deno.serve(async (req) => {
  if (req.headers.get("x-hook-secret") !== Deno.env.get("HOOK_SECRET")) return new Response("no", { status: 401 });
  const { record: f } = await req.json(); if (!f) return new Response("ok");
  const d = JSON.stringify(f.diag || {}).slice(0, 1500);

  // ── 0단계: 규칙 (토큰 0)
  if (f.kind === "solved") { await upd(f.id, { level: 0, status: "done" }); return new Response("ok"); }
  if (f.kind === "auto") {                         // 자동 오류: 같은 오류는 6시간에 1번만, 3건 이상 쌓이면 알림
    const n = await recentAutoSame(f.msg);
    await upd(f.id, { level: 0, status: "done" });
    if (n === 3 || n === 10 || n === 30) await tg(`🚨 같은 오류 ${n}건 (6시간)\n${f.msg}\n${d}`);
    return new Response("ok");
  }
  if (!AK) { await tg(`📮 [${f.kind}] ${f.msg}\n${d}`); await upd(f.id, { status: "waiting_owner", level: 3 }); return new Response("ok"); }

  // ── 1단계: Haiku — 분류 + 쉬운 건 바로 답장
  const h = await claude("claude-haiku-5-5",
    `${APP}\n사용자 문의를 분류해 JSON만 출력: {"sev":0-3,"spam":bool,"easy":bool,"reply":"냥이 말투 한국어(또는 사용자 언어) 2~3문장 답, easy일 때만","why":"한 줄"}
sev: 0 의견/칭찬, 1 사용법 질문, 2 버그 의심·데이터 문제, 3 앱이 안 됨/다수 영향. 사용법으로 해결되면 easy=true.`,
    `종류:${f.kind}\n내용:${f.msg}\n진단:${d}`, 300);
  if (h.spam) { await upd(f.id, { level: 0, status: "done", triage: h }); return new Response("ok"); }
  if (h.easy && h.reply && (h.sev ?? 2) <= 1) {
    await upd(f.id, { level: 1, status: "auto_replied", triage: h, reply: h.reply, replied_at: new Date().toISOString() });
    if (f.kind === "idea" || h.sev === 0) await tg(`💡 [${f.kind}] ${f.msg}`);
    return new Response("ok");
  }

  // ── 2단계: Sonnet — 진단 + 답장 + 운영자 필요 여부
  const s = await claude("claude-sonnet-5-5",
    `${APP}\n너는 1차 지원 엔지니어. JSON만: {"cause":"추정 원인","reply":"사용자에게 줄 냥이 말투 답(임시 해결책 포함, 3~4문장)","owner":bool,"fix":"운영자가 고칠 내용 한두 줄"}
owner=true: 코드 수정·문제 데이터 수정이 필요하거나 데이터 유실·다수 영향일 때.`,
    `종류:${f.kind}\n내용:${f.msg}\n진단:${d}\n1차분류:${JSON.stringify(h)}`, 600);
  const owner = !!s.owner || (h.sev ?? 0) >= 3;
  await upd(f.id, { level: owner ? 3 : 2, status: owner ? "waiting_owner" : "auto_replied", triage: { h, s },
    reply: s.reply || null, replied_at: s.reply ? new Date().toISOString() : null });

  // ── 3단계: 운영자 호출 → Claude Code(Opus)에 그대로 붙여넣기
  if (owner) await tg(`🆘 운영자 필요 (sev ${h.sev})\n문의: ${f.msg}\n추정: ${s.cause}\n수정: ${s.fix}\n\n👉 Claude에 붙여넣기:\n"암기냥이 문의 ${f.id} 고쳐줘. ${s.fix}"\n${d}`);
  return new Response("ok");
});
