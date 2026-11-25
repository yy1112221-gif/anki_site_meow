#!/usr/bin/env python3
"""ops/pending.json: 예약 작업이 켜질지 말지 정하는 일감 개수(AI·API 호출 없음, 공개 저장소라 숫자만)."""
import json, os, re, sys, time, urllib.request
from datetime import datetime, timezone, timedelta
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.environ.get("GITHUB_REPOSITORY", "yy1112221-gif/anki_site_meow")
SB = "https://cgupivfptuzqyadhqhiz.supabase.co"
SB_KEY = "sb_publishable_N-aZnP5Sdvuk5bjsNKE3mw_2dmnqgd2"

def get(url, headers=None, data=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode() or "null")

def requests_counts():
    txt = open(os.path.join(ROOT, "ops", "requests.md"), encoding="utf-8").read()
    body = txt.split("## 목록", 1)[-1].split("## 기록", 1)[0]
    now = datetime.now(timezone(timedelta(hours=9)))
    open_n = len(re.findall(r"^- \[ \]", body, re.M))
    for m in re.finditer(r"^- \[~\] (\d\d)-(\d\d) (\d\d):(\d\d)", body, re.M):   # 55분 넘게 멈춘 진행 중 = 다시 맡을 일
        mo, d, h, mi = map(int, m.groups())
        try:
            t = now.replace(month=mo, day=d, hour=h, minute=mi, second=0, microsecond=0)
            if (now - t).total_seconds() > 55 * 60: open_n += 1
        except ValueError: pass
    return open_n, len(re.findall(r"^- \[\?\]", body, re.M))

def pr_counts():
    tok = os.environ.get("GITHUB_TOKEN")
    if not tok: return None, None
    h = {"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"}
    prs = get(f"https://api.github.com/repos/{REPO}/pulls?state=open&per_page=50", h) or []
    data = 0
    for p in prs:
        files = get(f"https://api.github.com/repos/{REPO}/pulls/{p['number']}/files?per_page=100", h) or []
        if any(re.match(r"^(presets|slang)/", f["filename"]) for f in files): data += 1
    return len(prs), data

def inquiries_new():
    sec = os.environ.get("FB_ADMIN_SECRET")
    if not sec: return None
    try:
        rows = get(f"{SB}/rest/v1/rpc/fb_admin_list", {"apikey": SB_KEY, "Content-Type": "application/json"}, json.dumps({"p_secret": sec}).encode())
        return len([r for r in (rows or []) if r.get("status") == "new"])
    except Exception as e:
        print("inquiries:", type(e).__name__, file=sys.stderr); return None

def main():
    ro, rb = requests_counts(); po, pd = pr_counts(); iq = inquiries_new()
    out = {"requests_open": ro, "requests_blocked": rb, "prs_open": po, "prs_data": pd, "inquiries_new": iq}
    path = os.path.join(ROOT, "ops", "pending.json")
    old = {}
    try: old = json.load(open(path, encoding="utf-8"))
    except Exception: pass
    if {k: old.get(k) for k in out} == out and "--force" not in sys.argv:
        print("변화 없음", out); return
    out["at"] = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M KST")
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1); open(path, "a").write("\n")
    print("갱신", out)

if __name__ == "__main__": main()
