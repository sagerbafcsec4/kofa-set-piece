#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本番へ送る台本（記録の確認 → GitHubへ送信 → Cloudflareへ反映 → 中身の照合）

これ1本で「送り忘れ」「送ったつもり」を防ぐ。
Cloudflare は GitHub と連動していないため、GitHub に記録しただけでは
本番サイトは古いまま。この台本は最後に公開URLから実物を取り直して
手元と一致するかまで確かめる。

使い方:
    python deploy.py              通常（記録の確認 → 送信 → 反映 → 照合）
    python deploy.py --dry-run    実際には送らず、何が起きるかだけ表示
    python deploy.py --project 別名   Cloudflare側の枠の名前を明示する

既定では、このフォルダ名を Cloudflare の枠の名前として使う。
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

# 公開するファイル（存在するものだけ送る）
DEPLOY_FILES = ["index.html"]

BASE = os.path.dirname(os.path.abspath(__file__))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def say(mark, msg):
    print("%s %s" % (mark, msg))
    sys.stdout.flush()


def run(cmd, shell=False):
    """コマンドを実行して (終了コード, 出力) を返す。"""
    p = subprocess.run(cmd, shell=shell, cwd=BASE, capture_output=True)
    out = (p.stdout + p.stderr).decode("utf-8", errors="replace").strip()
    return p.returncode, out


def norm(b):
    """改行の書き方の違いを無視して中身を比べるための指紋。"""
    return hashlib.md5(b.replace(b"\r\n", b"\n")).hexdigest()


def fetch(url, tries=5, wait=5):
    """公開URLから実物を取り直す（反映待ちのため数回ためす）。"""
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(
                url + "?_=" + str(int(time.time() * 1000)),
                headers={"User-Agent": "deploy-check", "Cache-Control": "no-cache"},
            )
            return urllib.request.urlopen(req, timeout=60).read()
        except Exception as e:
            last = e
            if i < tries - 1:
                time.sleep(wait)
    raise last


def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args
    project = os.path.basename(BASE)
    if "--project" in args:
        project = args[args.index("--project") + 1]
    site = "https://%s.pages.dev/" % project

    print("=" * 62)
    say("📦", "送り先: %s" % site)
    say("📁", "作業フォルダ: %s" % BASE)
    if dry:
        say("🧪", "確認だけの実行です（実際には送りません）")
    print("=" * 62)

    # --- 1. 送るファイルの確定 -------------------------------------------
    files = [f for f in DEPLOY_FILES if os.path.isfile(os.path.join(BASE, f))]
    missing = [f for f in DEPLOY_FILES if f not in files]
    if not files:
        say("✘", "送るファイルが1つも見つかりません: %s" % "、".join(DEPLOY_FILES))
        return 1
    say("①", "送るファイル: %s" % "、".join(files))
    if missing:
        say("　", "（見つからず飛ばす: %s）" % "、".join(missing))

    # --- 2. 未記録の変更がないか ------------------------------------------
    code, out = run(["git", "-c", "core.quotepath=false", "status", "--porcelain"])
    if code != 0:
        say("✘", "保管庫の状態を確認できません: %s" % out)
        return 1
    dirty = [l for l in out.splitlines()
             if l.strip() and not l.startswith("??")]
    if dirty:
        say("✘", "まだ記録していない変更があります。先に記録してください:")
        for l in dirty:
            print("      " + l)
        say("　", "（例）git add <ファイル名> のあと git commit")
        return 1
    # 送るファイルそのものが記録済みか、1本ずつ確かめる
    unsaved = []
    for f in files:
        code, st = run(["git", "-c", "core.quotepath=false",
                        "status", "--porcelain", "--", f])
        if code == 0 and st.strip():
            unsaved.append(f + "（" + st.strip().split("\n")[0] + "）")
    if unsaved:
        say("✘", "送るファイルが記録されていません。先に記録してください:")
        for u in unsaved:
            print("      " + u)
        return 1
    say("②", "未記録の変更なし（送るファイルも記録済み）")

    # --- 3. GitHubへ未送信の記録がないか ----------------------------------
    run(["git", "fetch", "origin", "main"])
    code, ahead = run(["git", "rev-list", "--count", "origin/main..HEAD"])
    n_ahead = int(ahead) if code == 0 and ahead.isdigit() else 0
    if n_ahead:
        say("③", "GitHubへ未送信の記録が %d 件あります → 送ります" % n_ahead)
        if dry:
            say("　", "（確認だけの実行なので送りません）")
        else:
            code, out = run(["git", "push", "origin", "main"])
            if code != 0:
                say("✘", "GitHubへ送れませんでした: %s" % out)
                return 1
            say("　", "GitHubへ送りました")
    else:
        say("③", "GitHubへの記録は最新です")

    # --- 4. 送る中身を組み立てる ------------------------------------------
    tmp = tempfile.mkdtemp(prefix="deploy_")
    for f in files:
        shutil.copy2(os.path.join(BASE, f), os.path.join(tmp, f))
    say("④", "送る中身を用意しました（%d ファイル）" % len(files))

    # --- 5. Cloudflareへ反映 ----------------------------------------------
    if dry:
        say("⑤", "ここで本番へ送ります（確認だけの実行なので送りません）")
        shutil.rmtree(tmp, ignore_errors=True)
        return 0
    cmd = ('npx wrangler pages deploy "%s" --project-name=%s '
           "--branch=main --commit-dirty=true" % (tmp, project))
    say("⑤", "本番へ送っています…（初回は少し時間がかかります）")
    code, out = run(cmd, shell=True)
    shutil.rmtree(tmp, ignore_errors=True)
    if code != 0:
        say("✘", "本番へ送れませんでした:")
        print(out)
        return 1
    for line in out.splitlines():
        if "Success" in line or "Deployment complete" in line:
            print("      " + line.strip())

    # --- 6. 公開URLから取り直して照合 --------------------------------------
    say("⑥", "本番の中身を取り直して、手元と一致するか確かめます…")
    ok = True
    for f in files:
        local = open(os.path.join(BASE, f), "rb").read()
        try:
            live = fetch(site + f)
        except Exception as e:
            say("　✘", "%s を本番から取れませんでした: %s" % (f, e))
            ok = False
            continue
        if norm(local) == norm(live):
            say("　✔", "%s 一致" % f)
        else:
            say("　✘", "%s ★中身が違います（手元 %d / 本番 %d バイト）"
                % (f, len(local), len(live)))
            ok = False

    print("=" * 62)
    if ok:
        say("✅", "完了。本番サイトは手元と同じ中身になりました。")
        say("　", "ブラウザで開くときは Ctrl+F5（強制再読み込み）で確認してください。")
        say("🌐", site)
        return 0
    say("⚠", "本番と手元が一致していません。少し待ってもう一度この台本を実行してください。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
