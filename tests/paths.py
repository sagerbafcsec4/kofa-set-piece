# -*- coding: utf-8 -*-
"""テストで使う住所を1か所に集める（日本語パスをコマンド行に出さないため）。"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT_DIR = os.path.join(HERE, "output")

# テスト用の実データ（Opta・ラ・リーガ・第6節）。tests/fixtures/ に置く（*.xlsx は保管庫に入れない設定なので手元だけ）
SRC_DIR = os.path.join(HERE, "fixtures")
GOALS = os.path.join(SRC_DIR, "6Goals.xlsx")
CONCEDED = os.path.join(SRC_DIR, "6Conceded.xlsx")

LEAGUE = "ラ・リーガ"
SEASON = "2026/27"
MATCHDAY = 6
EXPECTED_FILENAME = "ラ・リーガ_セットプレー情報_2627第6節.xlsx"

SHEET_CSV = ("https://docs.google.com/spreadsheets/d/e/2PACX-1vRfxZY4XyfVh5oL7Fk8nTF1wdhDdzcscTlL1ZTVpu2P2hJ_kg-abbu4HFziWrgkRRuTL-Q_TLxzFrlc"
             "/pub?gid=0&single=true&output=csv")

# 色付けテスト用の対戦（ホーム, アウェイ）。色はアプリ既定（試合1: 黄・黄緑／試合2: ピンク・青）
TEST_MATCHES = [("アラベス", "バレンシア"), ("レアル・マドリー", "エルチェ")]
TEST_MATCH_COLORS = [("FFFFFF00", "FF92D050"), ("FFFF9999", "FFB4C6E7")]
