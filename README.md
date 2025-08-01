# n8n-tiktok-uploader

TikTokへの動画投稿をn8nで自動化するためのプロジェクトです。
アクセストークンの管理をAWS Lambda + S3で行い、n8nから安全かつ自動的にTikTok APIを呼び出せる構成になっています。

---

## 🔧 ディレクトリ構成

```
n8n-tiktok-uploader/
├── lambda_token_api/             # Lambda側のAPI実装
│   ├── lambda_function.py        # Lambdaハンドラー（GET /token/{open_id}）
│   ├── token_store.py            # S3ベースのトークン管理（既存Python資産を移植）
│   ├── test_token_store.py       # ローカルテスト用コード
│   ├── requirements.txt          # Lambdaで使う依存ライブラリ
│   └── README.md
├── n8n-workflows/                # n8n側のワークフロー
│   ├── tiktok-upload.json        # エクスポートされたワークフロー
│   └── README.md
├── README.md                     # プロジェクト全体の説明
```

---

## 📦 使用技術

- AWS Lambda（Python 3.11）
- Amazon S3（トークンの永続化）
- n8n（ノーコード自動化プラットフォーム）
- TikTok Open API（動画投稿）

---

## 🚀 機能概要

- TikTokアクセストークンを安全にS3で管理
- Lambda経由でトークンをAPI化し、n8nから取得可能
- n8nで動画タイトルやバイナリを渡してアップロード

---

## 🏁 セットアップ手順（概要）

1. S3バケットを作成（例：`tiktok-token-store`）
2. `lambda_token_api/` 以下をzipにしてLambdaにデプロイ
3. API Gatewayで `GET /token/{open_id}` を公開
4. n8nワークフローをインポートし、HTTP RequestノードでAPIを叩く

---

## 📄 ライセンス

MIT License（または未定）

---

このREADMEはプロジェクト全体の概要なので、各ディレクトリにあるREADMEも参照してください。