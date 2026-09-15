#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ブラウザで一気通貫に試す台本（Playwright）。

  1. このフォルダを http://localhost:8788/ で配る（file:// だと外部部品・辞書CSVの取得が不安定なため）
  2. 得点用・失点用の実データをアップロード → ラ・リーガ／2026/27／第5節 → 実行
  3. ダウンロードされたファイル名が期待どおりか確認し tests/output に保存
  4. verify_output.verify() で中身を機械照合

使い方:  python tests\\e2e_run.py [--headed]
"""
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths  # noqa: E402
import verify_output  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PORT = 8788

# ブラウザ内の純関数（window.KSP）を直接叩く部品テスト。
# 共有シートに「Opta表記」列がまだ無くても、日本語化・並び替え・CSV読みが正しいことを確かめる。
UNIT_JS = r"""
() => {
  const out = [];
  const t = (name, cond, detail) => out.push({name, ok: !!cond, detail: String(detail ?? "")});
  // parseCSV: 引用符・カンマ入り・"" エスケープ・BOM・CRLF
  const rows = KSP.parseCSV('﻿チーム名,所属リーグ,Opta表記\r\n"ブライトン",プレミアリーグ,"Brighton & Hove Albion;Brighton"\r\n"A ""B"" c",x,y\r\n');
  t("parseCSV 行数", rows.length === 3, rows.length);
  t("parseCSV 引用符内のカンマ・セミコロン", rows[1][2] === "Brighton & Hove Albion;Brighton", rows[1][2]);
  t("parseCSV 二重引用符のエスケープ", rows[2][0] === 'A "B" c', rows[2][0]);
  // buildDictionary: 選択リーグだけ・;区切り・NFC・大小無視
  const header = ["チーム名","所属リーグ","別表記","Opta表記"];
  const data = [
    ["レアル・マドリー","ラ・リーガ","レアル・マドリード","Real Madrid"],
    ["アトレティコ・デ・マドリー","ラ・リーガ","","Atlético de Madrid"],   // NFD で登録されていても一致させる
    ["ブライトン","プレミアリーグ","","Brighton & Hove Albion;Brighton"],
    ["ベティス","ラ・リーガ","","Real Betis"],
  ];
  const d0 = KSP.buildDictionary([], [], "ラ・リーガ");
  t("内蔵表だけで日本語化できる", d0.builtin === 20 && d0.map.get(KSP.normKey("Real Madrid")) === "レアル・マドリー" && d0.map.get(KSP.normKey("Sevilla")) === "セビージャ", JSON.stringify([d0.builtin, d0.map.get(KSP.normKey("Sevilla"))]));
  t("内蔵表 3リーグ", KSP.BUILTIN_DICT["プレミアリーグ"].length === 20 && KSP.BUILTIN_DICT["エールディヴィジ"].length === 18, "");
  const header2 = ["チーム名","所属リーグ","Opta表記"];
  const dOv = KSP.buildDictionary(header2, [["レアル・マドリード","ラ・リーガ","Real Madrid"]], "ラ・リーガ");
  t("シートの登録が内蔵表より優先", dOv.map.get(KSP.normKey("Real Madrid")) === "レアル・マドリード" && dOv.duplicates.length === 0 && dOv.fromSheet === 1, JSON.stringify([dOv.map.get(KSP.normKey("Real Madrid")), dOv.duplicates]));
  const d = KSP.buildDictionary(header, data, "ラ・リーガ");
  t("辞書 リーグ絞り込み", d.teamsInLeague === 3 && d.fromSheet === 3, JSON.stringify([d.teamsInLeague, d.fromSheet]));
  t("辞書 Opta表記列あり", d.sheetHasColumn === true, d.sheetHasColumn);
  t("辞書 NFC 正規化", d.map.get(KSP.normKey("Atlético de Madrid")) === "アトレティコ・デ・マドリー", d.map.get(KSP.normKey("Atlético de Madrid")));
  t("辞書 他リーグの行は入らない（内蔵表にも無い英語名で確認）", !d.map.has(KSP.normKey("Brighton")), d.map.has(KSP.normKey("Brighton")));
  const dNo = KSP.buildDictionary(["チーム名","所属リーグ"], [["x","ラ・リーガ"]], "ラ・リーガ");
  t("辞書 列なしでも内蔵表で動く", dNo.sheetHasColumn === false && dNo.map.size > 0, JSON.stringify([dNo.sheetHasColumn, dNo.map.size]));
  // localizeAndSort: 日本語化・未登録・並び（SP降順→Total降順→名前昇順）
  const rowsIn = [
    {team:"Unknown FC", setPiece:4, total:9, penalty:0,corner:0,direct:0,indirect:0,throwIn:0,setPiecePct:0.5},
    {team:"REAL MADRID", setPiece:3, total:14, penalty:0,corner:0,direct:0,indirect:0,throwIn:0,setPiecePct:0.2},
    {team:"Real Betis", setPiece:3, total:14, penalty:0,corner:0,direct:0,indirect:0,throwIn:0,setPiecePct:0.2},
    {team:"Atlético de Madrid", setPiece:3, total:20, penalty:0,corner:0,direct:0,indirect:0,throwIn:0,setPiecePct:0.1},
  ];
  const ls = KSP.localizeAndSort(rowsIn, d.map);
  t("日本語化 大小無視", ls.rows.some(r => r.name === "レアル・マドリー"), ls.rows.map(r=>r.name).join("|"));
  t("未登録は英語のまま＋一覧", ls.unknown.length === 1 && ls.unknown[0] === "Unknown FC" && ls.rows[0].name === "Unknown FC", JSON.stringify(ls.unknown));
  t("並び SP降順→Total降順→名前昇順", ls.rows.map(r=>r.name).join("|") === "Unknown FC|アトレティコ・デ・マドリー|ベティス|レアル・マドリー", ls.rows.map(r=>r.name).join("|"));
  // 表題の注記（自由文言）
  const wbT = KSP.buildWorkbook({ goals: [rowsIn[1]], conceded: [rowsIn[1]], league: "ラ・リーガ", season: "2026/27", matchday: 5, provisional: true });
  t("暫定チェックで表題に「暫定」", wbT.ws.getCell(1,1).value === "セットプレーからの得点数 (Opta) ※第5節終了時暫定" && wbT.ws.getCell(5,1).value === "セットプレーからの失点数 (Opta) ※第5節終了時暫定", wbT.ws.getCell(1,1).value);
  const wbD = KSP.buildWorkbook({ goals: [rowsIn[1]], conceded: [rowsIn[1]], league: "ラ・リーガ", season: "2026/27", matchday: 5 });
  t("チェックなしなら「第5節終了時」", wbD.ws.getCell(1,1).value === "セットプレーからの得点数 (Opta) ※第5節終了時", wbD.ws.getCell(1,1).value);
  // 全セル照合: 正しい表は一致、わざと1セル壊すと検知
  const srcM = new Map([[KSP.normKey("Real Madrid"), {setPiece:3, penalty:0, corner:0, direct:0, indirect:0, throwIn:0, setPiecePct:20}]]);
  const okRow = [{team:"Real Madrid", name:"レアル・マドリー", setPiece:3, total:14, penalty:0, corner:0, direct:0, indirect:0, throwIn:0, setPiecePct:0.2}];
  const wbV = KSP.buildWorkbook({ goals: okRow, conceded: okRow, league: "ラ・リーガ", season: "2026/27", matchday: 5 });
  const cmpOk = KSP.compareAllCells(wbV.ws, 3, 3, okRow, srcM);
  t("全セル照合 正しい表は一致", cmpOk.ok && cmpOk.total === 8, JSON.stringify(cmpOk));
  wbV.ws.getCell(3, 4).value = 9;   // Corners を書き換え
  const cmpNg = KSP.compareAllCells(wbV.ws, 3, 3, okRow, srcM);
  t("全セル照合 1セルの改変を検知", !cmpNg.ok && cmpNg.bad.length === 1 && /D3/.test(cmpNg.bad[0]), JSON.stringify(cmpNg.bad));
  // まとめて貼り付け（区切り: 空白 / vs / -）。matchList を直接使うので前後で空にする
  KSP.matchList.length = 0;
  document.querySelector("#league").value = "ラ・リーガ";   // 貼り付けは画面で選んだリーグの登録名で照合する
  const imp = KSP.importPastedMatches("アラベス バレンシア\nレアル・マドリー vs エルチェ\nバルセロナ - ラシン・サンタンデール\n知らないFC セビージャ");
  t("貼り付け 取り込み数", imp.added === 4 && KSP.matchList.length === 4, JSON.stringify(imp));
  t("貼り付け 区切り3種", KSP.matchList[0].home === "アラベス" && KSP.matchList[0].away === "バレンシア" && KSP.matchList[1].away === "エルチェ" && KSP.matchList[2].away === "ラシン・サンタンデール", JSON.stringify(KSP.matchList.map(m => [m.home, m.away])));
  t("貼り付け 一致しない名前は空欄＋報告", KSP.matchList[3].home === "" && KSP.matchList[3].away === "セビージャ" && imp.miss.length === 1, JSON.stringify(imp.miss));
  t("貼り付け 既定の色は試合順（黄・黄緑／ピンク・青）", KSP.matchList[0].homeColor === "yellow" && KSP.matchList[0].awayColor === "lime" && KSP.matchList[1].homeColor === "pink" && KSP.matchList[1].awayColor === "blue", JSON.stringify(KSP.matchList.map(m => [m.homeColor, m.awayColor])));
  KSP.matchList.length = 0;
  // 色付け付きのブック: 2試合→表2組・該当行だけ塗り＋太字
  const rows2 = [
    {team:"Sevilla", name:"セビージャ", setPiece:4, total:9, penalty:0,corner:0,direct:0,indirect:0,throwIn:0,setPiecePct:0.5},
    {team:"Real Madrid", name:"レアル・マドリー", setPiece:3, total:14, penalty:0,corner:0,direct:0,indirect:0,throwIn:0,setPiecePct:0.2},
    {team:"Elche", name:"エルチェ", setPiece:1, total:5, penalty:0,corner:0,direct:0,indirect:0,throwIn:0,setPiecePct:0.1},
  ];
  const wbH = KSP.buildWorkbook({ goals: rows2, conceded: rows2, league: "ラ・リーガ", season: "2026/27", matchday: 5,
    matches: [{home:"セビージャ", away:"エルチェ", homeColor:"FFFFFF00", awayColor:"FF92D050"}, {home:"レアル・マドリー", away:"エルチェ", homeColor:"FFFF9999", awayColor:"FFB4C6E7"}] });
  const fillOf = (r, c) => (wbH.ws.getCell(r, c).fill && wbH.ws.getCell(r, c).fill.fgColor) ? wbH.ws.getCell(r, c).fill.fgColor.argb : null;
  t("色付け 表が2組（J列に2組目）", wbH.ws.getCell(1, 10).value === wbH.ws.getCell(1, 1).value && wbH.layout.blocks.length === 2, wbH.ws.getCell(1, 10).value);
  t("色付け 1組目: セビージャ黄・エルチェ黄緑・レアル無色", fillOf(3, 1) === "FFFFFF00" && fillOf(3, 8) === "FFFFFF00" && fillOf(5, 1) === "FF92D050" && fillOf(4, 1) === null && wbH.ws.getCell(3, 1).font.bold === true && wbH.ws.getCell(4, 1).font.bold === false, JSON.stringify([fillOf(3,1), fillOf(4,1), fillOf(5,1)]));
  t("色付け 2組目: レアルピンク・エルチェ青・セビージャ無色", fillOf(4, 10) === "FFFF9999" && fillOf(5, 10) === "FFB4C6E7" && fillOf(3, 10) === null, JSON.stringify([fillOf(3,10), fillOf(4,10), fillOf(5,10)]));
  t("色付け 失点表にも同じ色", fillOf(9, 1) === "FFFFFF00" && fillOf(10, 10) === "FFFF9999", JSON.stringify([fillOf(9,1), fillOf(10,10)]));
  // makeFileName
  t("ファイル名", KSP.makeFileName("ラ・リーガ","2026/27",5) === "ラ・リーガ_セットプレー情報_2026-27_第5節.xlsx", KSP.makeFileName("ラ・リーガ","2026/27",5));
  t("ファイル名（暫定）", KSP.makeFileName("ラ・リーガ","2026/27",5,true) === "ラ・リーガ_セットプレー情報_2026-27_第5節暫定.xlsx", KSP.makeFileName("ラ・リーガ","2026/27",5,true));
  return out;
}
"""


def run_unit_tests(page):
    page.wait_for_function("typeof window.KSP === 'object'", timeout=20000)
    results = page.evaluate(UNIT_JS)
    # 内蔵表（index.html）と docs/opta-names-draft.csv が同内容か
    import csv
    builtin = page.evaluate("KSP.BUILTIN_DICT")
    flat_builtin = sorted((lg, n, o) for lg, pairs in builtin.items() for n, o in pairs)
    with open(verify_output.BUILTIN_CSV, encoding="utf-8-sig") as f:
        flat_csv = sorted((r["所属リーグ"], r["チーム名"], r["Opta表記"]) for r in csv.DictReader(f))
    results.append({"name": "内蔵表と docs/opta-names-draft.csv が同内容", "ok": flat_builtin == flat_csv,
                    "detail": f"内蔵 {len(flat_builtin)} / CSV {len(flat_csv)}"})
    ok = True
    for r in results:
        print(("✔ " if r["ok"] else "✘ ") + "[部品] " + r["name"] + ("" if r["ok"] else "  — " + r["detail"]))
        ok = ok and r["ok"]
    return ok


def main():
    headed = "--headed" in sys.argv
    from playwright.sync_api import sync_playwright

    os.makedirs(paths.OUT_DIR, exist_ok=True)
    server = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
                              cwd=paths.REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.0)
    rc = 1
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=not headed)
            page = browser.new_page(accept_downloads=True)
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.goto(f"http://127.0.0.1:{PORT}/index.html")
            unit_ok = run_unit_tests(page)
            page.set_input_files("#fileGoals", paths.GOALS)
            page.set_input_files("#fileConceded", paths.CONCEDED)
            page.select_option("#league", paths.LEAGUE)
            page.select_option("#season", paths.SEASON)
            page.fill("#matchday", str(paths.MATCHDAY))
            page.wait_for_function("!document.querySelector('#run').disabled", timeout=40000)
            print("辞書:", page.inner_text("#dictStatus").strip())

            def run_once(label):
                with page.expect_download(timeout=60000) as dl:
                    page.click("#run")
                d = dl.value
                name = d.suggested_filename
                out_path = os.path.join(paths.OUT_DIR, label + "_" + name)
                d.save_as(out_path)
                page.wait_for_selector("#summary:not(:empty)", timeout=10000)
                print(f"[{label}] ダウンロード名: {name}")
                print(f"[{label}] 要約: " + page.inner_text("#summary").strip())
                print(f"[{label}] 照合表:\n" + page.inner_text("#checks").strip())
                w = page.inner_text("#warnings").strip()
                if w:
                    print(f"[{label}] 警告:\n" + w)
                return name, out_path

            # 1回目: 色付けなし
            name, out_path = run_once("plain")
            # 2回目: 色付けON → まとめて貼り付けで2試合
            page.check("#useHighlight")
            page.click("#clearMatches")
            page.fill("#pasteMatches", "\n".join(f"{h} {a}" for h, a in paths.TEST_MATCHES))
            page.click("#importMatches")
            print("貼り付け:", page.inner_text("#pasteResult").strip())
            page.wait_for_function("!document.querySelector('#run').disabled", timeout=10000)
            name_hl, out_hl = run_once("highlight")
            if errors:
                print("ブラウザのエラー:", errors)
            page.screenshot(path=os.path.join(paths.OUT_DIR, "screenshot.png"), full_page=True)
            browser.close()
        name_ok = name == paths.EXPECTED_FILENAME and name_hl == paths.EXPECTED_FILENAME
        print(("✔" if name_ok else "✘") + " ファイル名が期待どおり", name, "/", name_hl, "/ 期待:", paths.EXPECTED_FILENAME)
        ok, text = verify_output.verify(out_path)
        print("=== 色付けなし ===\n" + text)
        ok2, text2 = verify_output.verify(out_hl, matches=paths.TEST_MATCHES, match_colors=paths.TEST_MATCH_COLORS)
        print("=== 色付けあり（2試合） ===\n" + text2)
        rc = 0 if (ok and ok2 and name_ok and unit_ok and not errors) else 1
    finally:
        server.terminate()
    print("RESULT:", "PASS" if rc == 0 else "FAIL")
    return rc


if __name__ == "__main__":
    sys.exit(main())
