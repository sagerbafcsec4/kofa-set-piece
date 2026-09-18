# セットプレーExcel作成（kofa-set-piece）

Optaの「What Scored - Goals」「What Conceded - Goals」の2つのExcelを落とすだけで、
日本語クラブ名・決まった体裁の「セットプレー情報」Excelを作るWebアプリ。

公開URL（本体・Cloudflare Pages・鍵つき）: https://kofa-set-piece.pages.dev/
（鍵＝Cloudflare Access。Zero Trust → Access → Applications に Self-hosted「kofa-set-piece.pages.dev」を作り、ポリシー「会社ドメイン許可」を付けた。2026-09-15設定済み。Pages側の設定画面に「Access Policy」ボタンは無かったので、Zero Trust 側で直接作る）

処理はすべて利用者のブラウザ内で完結し、Optaのファイルは外部送信されない。
ネットから読みに行くのは「チーム名辞書」（Googleスプレッドシートの公開CSV）と、Excelを作る部品（ExcelJS）だけ。

---

## ⚠ 修正する人へ（最重要）

**画面もロジックも `index.html` 1枚に全部入っています（唯一の正本）。**

修正手順:
1. `index.html` を編集する
2. `python tests\e2e_run.py` で一気通貫テスト（部品テスト → ブラウザでアップ・実行・ダウンロード → 出力の機械照合）が `RESULT: PASS` になることを確認する
3. このリポジトリにコミット・プッシュ（GitHubが正本）
4. **Cloudflare Pagesは自動反映されない**（GitHub連携ではなく手動配置のため。他のkofaアプリと同じ方式）。反映するには
   `本番へ送る.bat` をダブルクリック（＝ `python deploy.py`。未記録の変更がないか確かめ → GitHubへ送信 → `index.html` だけを一時フォルダに置いて
   `npx wrangler pages deploy <一時フォルダ> --project-name=kofa-set-piece --branch=main` → 公開URLから取り直して中身を照合）。
   初回のみ `npx wrangler login` でのログインが必要。古い表示が出たら Ctrl+F5。
   ⑥の照合が「証明書」のエラーで失敗することがある（2026-09-14 初回公開時に発生。送信自体は成功していた）。
   その場合はブラウザで公開URLを開き、画面が最新か（Ctrl+F5）を目で確認すればよい。
   さらに 2026-09-15 以降は鍵（Access）が掛かっているため、⑥は常に「取れない／不一致」になる。⑤の「Deployment complete」が出ていれば送信は成功。最終確認は自分のブラウザでログインして Ctrl+F5。
   **注意**: `wrangler pages project create` は新方式（Workers統合）に流れるため、枠を作り直すときだけ `--force` を付ける（初回に誤って新方式で作ってしまい撤去した経緯あり）。

別のPC・別のClaude/Coworkで作業するときも、**まずこの README と `index.html` を読めば全体を把握できます。**

---

## 絶対ルール（データ保護）

- Optaの数値は**書き換えない**。やるのは「並べ替え」「クラブ名を日本語に置換」「割合の列に全角％の表示形式を付ける」だけ。
- 出力前に**出来上がった表の全セル（クラブ名＋数値7列×全クラブ×得点・失点＝20クラブなら320セル）を、元ファイルを別経路で読み直した値と1つずつ自動照合**する（`readOptaMatrix` → `compareAllCells`）。1か所でも違えばファイルを出さず、不一致セルを「処理の詳細」に一覧する（2026-09-15強化）。あわせて Total 列の合計照合も行う。
- 元ファイルは変更せず、別ファイル（`{リーグ}_セットプレー情報_{シーズン}第{節}節.xlsx`）をダウンロードする方式。
- 実データ（`*.xlsx`）はこのリポジトリに入れない（`.gitignore` 済み）。

## 入力ファイルの前提

- Optaから落とした `.xlsx`。シート名は `Sheet`（無ければ先頭シート）。1行目が見出し。
- 必要な列（**名前で探す**ので順番は問わない。大文字小文字・空白のゆれは吸収）:
  `Team Name` / `Goals From Set Piece` / `Goals From Penalties` / `Goals From Corner` / `Goals From Direct Freekicks` / `Goals from Indirect Freekicks` / `Goals From Throw In` / `Total` / `Goals From Set Piece %`
- 得点用・失点用の2枠。まとめてどちらかに落とすと、ファイル名に `Conceded` を含む方を失点用に自動で振り分ける。
- 列が足りない・数値でない・Excelのエラー値がある場合は、理由を表示して中止する。

## チーム名辞書（内蔵表＋共有スプレッドシートで上書き）

- **土台はアプリ内蔵の対応表** `BUILTIN_DICT`（`index.html`。Optaの英語名 → 日本語名。プレミア20・ラ・リーガ20・エールディヴィジ18）。
  日本語名は共有シートの「チーム名」列と同じ表記。`docs/opta-names-draft.csv` は同内容の写し（テストで一致を照合）。
- **共有シートに「Opta表記」列があれば、そちらを優先**する（Excelフォーマット作成アプリと同じ共有スプレッドシート・公開CSV。URLは `SHEET_CSV`）。
  使う列: `チーム名`／`所属リーグ`／`Opta表記`（`;` 区切りで複数可。大文字小文字・前後の空白は無視）。列を足すかどうかは任意。
- 表記を変えたい・クラブを増やしたいときの2通り: ①共有シートに「Opta表記」列を足して書く（アプリを触らない）②`BUILTIN_DICT` を直して `本番へ送る.bat`。
- 対応表に無いクラブは**英語のまま出力し、結果欄で警告**する（実行は止めない）。
- 共有シートが読めないとき（ネット断など）は内蔵表だけで動き、結果欄にその旨を出す。
- ラ・リーガの英語名は実データで確認済み。プレミア・エールディヴィジは**推定**（未登録警告が出た英語名をそのまま足せば直る）。
- リーグを増やすときは `LEAGUE_OPTIONS` と `BUILTIN_DICT` に足す（共有シート側に行があればそれも使われる）。

## 出力の仕様

| 項目 | 内容 |
|---|---|
| ファイル名 | `{リーグ}_セットプレー情報_{シーズン2桁2つ}第{節}節.xlsx`（例 `ラ・リーガ_セットプレー情報_2627第5節.xlsx`。2026-09-15短縮。旧: `…_2026-27_第5節.xlsx`） |
| シート名 | `{節}節用セットプレー` |
| 表題 | `セットプレーからの得点数 (Opta) ※第{節}節終了時`／`…失点数…`。「暫定」にチェックを入れると表題は `※第{節}節終了時暫定`、ファイル名は `…{シーズン}第{節}節暫定.xlsx`（シート名は変わらない。2026-09-15追加） |
| 配置 | 得点表: 1行目 表題（A:H結合）／2行目 見出し／3行目〜 本文。1行空けて失点表（20クラブなら 24〜45行目） |
| 見出し | Team / Total / Penalties / Corners / Direct Freekicks / Indirect Freekicks / Throw In / Goals From Set Piece ％（長いものは2行・％は全角。2026-09-15変更） |
| 列の対応 | Total←Goals From Set Piece、Penalty←…Penalties、Corners←…Corner、Dir.←…Direct Freekicks、Ind.←…Indirect Freekicks、Throws←…Throw In、％←…Set Piece % の値そのまま（42.86 のように。表示形式 `0.00"％"` で全角％を付ける。2026-09-15変更・旧は÷100して 0.00%） |
| 並び | セットプレー得点（失点）の降順 → 同点は Opta ファイルの並び（Rk順）をそのまま（2026-09-15変更。旧: Optaの Total 降順 → 日本語名の昇順） |
| 体裁 | 全セル MS UI Gothic・中央揃え・「縮小して全体を表示」（見出し行だけ「折り返し」＝2行表示）。表題: 薄灰 `E7E6E6`・黒太字12pt・四方太線。見出し: 黒背景・白太字。本文: 外周太線・内側細線。％列は `0.00"％"`（値は Opta の100倍値そのまま）。文字サイズ 表題12／見出し11／表13（全列同じ）。行の高さ 表題20／見出し30／表15／空き行30。列幅 A=25・B〜G=13・H=20.78（2026-09-15 第6節の元Excel「ラ・リーガ_セットプレー情報_2026-27_第5節.xlsx」に合わせた。初版はテンプレ実測値 Meiryo UI／21.7…） |

## 対戦チームの色付け（2026-09-15追加）

- 設定の「特定のチームに色付けをつけますか？」を ON → 試合の行（ホーム／アウェイのプルダウン＋それぞれの色）を入れる。「＋ 試合を追加」／「まとめて貼り付け」（1行1試合。空白・タブ・vs・- 区切り。選んだリーグの登録名または共有シートの「別表記」に完全一致した名前だけ入る）
- 出力: 試合の数だけ表を右へ複製（A〜H、J〜Q、S〜Z … 9列ピッチ・間に空き1列）。各表でその試合の2クラブの行（8セル）を塗り＋太字。得点表・失点表の両方
- 色は薄めの8色 `PALETTE`（黄 FFFF00／黄緑 92D050／ピンク FF9999／青 B4C6E7／オレンジ FFC58A／薄い黄 FFF2CC／薄い緑 C6EFCE／薄い紫 D9C3F0）。既定は試合順に 黄・黄緑 → ピンク・青 → オレンジ・薄い黄 → …。クラブごとにプルダウンで変更可
- 全セル照合は複製した表すべてに掛かる（結果欄「N／N セル一致（表 K 組）」）。指定クラブが表に無いときは警告
- 検査台本は `verify(..., matches=[(ホーム, アウェイ)], match_colors=[(ARGB, ARGB)])` で色付けまで照合する

## チーム一覧タブ（2026-09-15追加）

- 画面上部のタブ「チーム一覧」: 共有シートの クラブ名／所属リーグ／Opta表記 を一覧表示（リーグで絞り込み可。シートに英語名が無い行は内蔵表の値で補って表示）
- 「📝 共有スプレッドシートを開いて編集」ボタンで共有シートを別タブで開く（Excelフォーマット作成アプリと同じシート）。編集後は「再読込」

## 結果欄の照合（毎回表示）

- クラブ数（リーグの期待値と比較）／得点と失点でクラブの顔ぶれが同じか／Total の合計が元ファイルと一致／**全セル照合（N／N セル一致）**／対戦チームの色付け（指定クラブが表にあるか）／クラブ名の日本語化（未登録一覧）

## ファイル一覧

| ファイル | 役割 |
|---|---|
| `index.html` | アプリ本体（画面＋ロジック。**唯一の正本**） |
| `deploy.py` / `本番へ送る.bat` | 本番（Cloudflare Pages）へ送る台本 |
| `tests/e2e_run.py` | 一気通貫テスト（Playwright）。`python tests\e2e_run.py`。`--headed` でブラウザを表示 |
| `tests/verify_output.py` | 出力xlsxの機械照合（openpyxl）。単独でも実行可 |
| `tests/paths.py` | テスト用の実データの住所（`tests/fixtures/6Goals.xlsx`・`6Conceded.xlsx`。xlsx は保管庫に入れないので手元にコピーして置く） |
| `tests/excel_measure.ps1` | Excel本体で行高・列幅・文字を実測（表示設定の抜けなど openpyxl では見えない問題用） |
| `docs/opta-names-draft.csv` / `docs/opta-names-column.txt` | 内蔵表の写し（CSV）と、共有シートへ貼る場合用の1列テキスト（任意） |
| `docs/superpowers/specs/` | 設計書 |

## 配色

- イメージ色はオレンジ（`--p1:#ea580c → --p2:#f59e0b` のグラデーション。2026-09-15にユーザー指定で紫から変更）。kofa の他アプリは Word＝青、Excelフォーマット＝緑、Excelデータ加工＝紫で、それらと被らない色にしている。画面の作り（カード式・タブ）は Excelデータ加工／Excelフォーマット作成と同じ。

## 仕組み・技術メモ

- 素のHTML＋JavaScript。Excelの読み書きは [ExcelJS](https://github.com/exceljs/exceljs) **4.4.0**（cdnjs・バージョン固定）。Python/Pyodideは使わない（起動待ちなし）。
- ExcelJS の癖: 結合セルは `mergeCellsWithoutStyle` で結合し8セル個別に体裁を入れる／`alignment.vertical` は `'middle'`／列幅がちょうど 9 だと既定扱いで書き出されない（現在は 25/13 なので該当なし）／%は `Math.round(v*100)/10000` で丸める。
- **Excel の癖（2026-09-18 実測・重要）**: xlsx に表示設定 `<sheetViews>` が無いと、Excel（日本語環境）は `ht="15"` と書いてある行を **0.8倍（12）** で解釈する（表題20→16.1・見出し30→24・表15→12）。ExcelJS は `views` を指定しないと `<sheetViews>` を書き出さないため、`addWorksheet(name, { views:[{ state:"normal", zoomScale:85, zoomScaleNormal:85 }] })` で必ず書き出す。openpyxl はファイルの値（15）をそのまま返すので検査では見つからない → **Excel本体での実測は `tests\excel_measure.ps1`**（`python .claude/scripts/run_powershell.py -f tests\excel_measure.ps1` でObsidianの台本経由。結果は tests/output/excel_measure_result.txt）。倍率85%は元Excelに合わせた値
- openpyxl（検査側）の癖: 結合範囲の2番目以降は文字・塗りを持たない `MergedCell` として読まれ、外周罫線だけが合成される。検査台本はその見え方で照合している。
- 主な関数: `parseOptaRows`（列名解決）→ `buildDictionary`（辞書）→ `localizeAndSort` → `buildWorkbook`/`writeTable`（体裁）→ `verify`（照合）→ `download`。純関数は `window.KSP` に公開しておりテストから直接叩ける。
