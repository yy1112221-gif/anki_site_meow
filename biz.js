// 개인정보처리방침·이용약관 페이지: biz.json에 사업자 정보가 채워지면 #biz 자리에 표시
fetch("biz.json", { cache: "no-cache" }).then(r => r.ok ? r.json() : {}).then(b => {
  const el = document.getElementById("biz"); if (!el || !b || !b.regNo) return;
  const rows = [["상호", b.name], ["대표·개인정보 보호책임자", b.owner], ["사업자등록번호", b.regNo], ["통신판매업 신고번호", b.mailOrderNo], ["주소", b.address], ["이메일", b.email]].filter(x => x[1]);
  el.innerHTML = rows.map(x => `${x[0]}: ${String(x[1]).replace(/[<>&]/g, "")}`).join("<br>") + "<br>앱 왼쪽 아래 「문의」 버튼으로도 연락할 수 있습니다.";
}).catch(() => {});
