# -*- coding: utf-8 -*-
"""テストで使う住所を1か所に集める（日本語パスをコマンド行に出さないため）。"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT_DIR = os.path.join(HERE, "output")

# テスト用の実データ（Opta・ラ・リーガ・第5節）
SRC_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "セットプレー")
GOALS = os.path.join(SRC_DIR, "#5Goals.xlsx")
CONCEDED = os.path.join(SRC_DIR, "#5Conceded.xlsx")

LEAGUE = "ラ・リーガ"
SEASON = "2026/27"
MATCHDAY = 5
EXPECTED_FILENAME = "ラ・リーガ_セットプレー情報_2026-27_第5節.xlsx"

SHEET_CSV = ("https://docs.google.com/spreadsheets/d/e/2PACX-1vRfxZY4XyfVh5oL7Fk8nTF1wdhDdzcscTlL1ZTVpu2P2hJ_kg-abbu4HFziWrgkRRuTL-Q_TLxzFrlc"
             "/pub?gid=0&single=true&output=csv")
