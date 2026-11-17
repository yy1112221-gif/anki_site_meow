# ANKI SITE MEOW（暗記して ミヤオウ / 암기냥이）

単語を入れるだけで、間隔反復（1→7→21→60→150日）の復習スケジュールを組む暗記アプリ。
静的サイト（HTML 1枚 + PWA）なので、GitHub Pages にそのまま置けば動きます。

## 更新しても利用者のデータが消えない理由
- 単語・進み具合は各利用者の端末のブラウザ（localStorage キー `focus-vocab-v1`）に保存されます。
- サイトのファイルを差し替えても、**同じURL（ドメイン）で配信している限り** データはそのまま残ります。
- 守ること:
  1. `LS_KEY`（`focus-vocab-v1`）を変えない
  2. リポジトリ名・URLを変えない（変えると別サイト扱いになりデータが見えなくなる）
  3. カードに項目を足すときは `newCard()` に既定値を入れ、古いデータでも動くようにする
- 更新は sw.js が「ネット優先」で取りに行くので、利用者が次に開いたときに反映されます。

## 外部サービス
- 例文: Tatoeba API（CC BY 2.0 FR）
- 翻訳: MyMemory
- 英語の意味: Wiktionary REST API

## 単語セットの出典 / 단어 세트 출처
- スペイン語 / 스페인어: ELELex (CEFRLex, UCLouvain) — CC BY-NC-SA 4.0 — https://cental.uclouvain.be/cefrlex/elelex/ （各語の最初に出たレベルで分類・内容語のみ）
- 日本語 / 일본어: JLPT 語彙（tanos.co.uk, Jonathan Waller, CC BY）via open-anki-jlpt-decks (MIT) — https://github.com/jamsinclair/open-anki-jlpt-decks
- 韓国語 / 한국어: 한국어기초사전 (국립국어원) — CC BY-SA 2.0 KR — https://krdict.korean.go.kr/ （日本語訳・例文を含む）
