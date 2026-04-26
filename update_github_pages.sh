#!/bin/bash

# リポジトリのディレクトリに移動
cd /home/pi/Desktop/cotoha/cotoha-weather.github.io

# Pythonスクリプトの実行
python test.py

sleep 7

python create_plot.py

sleep 7

# 現在の日時を取得
current_date=$(date +"%Y-%m-%d %H:%M:%S")

# 変更をステージングエリアに追加
git add .

# コミット（コミットメッセージに現在の日時を含める）
git commit -m "Update: $current_date"

# リモートリポジトリにプッシュ
git pull origin main
git push origin main

original="index.html"
backup="backup_index.html"

cp "$backup" "$original"
