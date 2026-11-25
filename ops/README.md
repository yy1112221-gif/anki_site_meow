# ops/ — 예약 작업이 싸게 도는 자리

- `requests.md`: ① 제작 요청함(원본). `- [ ]` 줄이 있을 때만 ① 제작(Opus)이 일함.
- `pending.json`: GitHub Actions `ops-scan`(2시간마다, AI 없음)이 만드는 일감 개수. **API를 부르지 않고 숫자만 적는다.** 예약 작업은 맨 먼저 이 파일(또는 requests.md)만 보고 0이면 바로 끝낸다.
  - `requests_open` 요청함 `[ ]`·멈춘 `[~]` 줄 수 · `requests_blocked` `[?]` 줄 수
  - `prs_open` 열린 PR 수 · `prs_data` 그중 presets/slang(검수 필요) PR 수
  - `inquiries_new` 답 안 한 문의 수(저장소 Secrets에 `FB_ADMIN_SECRET`이 있을 때만, 없으면 null)
- 공개 저장소라 개수만 적는다. 문의 내용·사용자 데이터는 여기 쓰지 않는다.
