# Lambda Token API

AWS LambdaでTikTokアクセストークンを管理・提供するAPIです。
n8nから安全にトークンを取得するためのエンドポイントを提供します。

## 機能

- TikTokアクセストークンをS3で安全に管理
- 期限切れトークンの自動更新
- n8n向けのRESTful API提供

## API エンドポイント

### GET /token/{open_id}

指定されたopen_idのアクセストークンを取得します。

**パラメータ:**
- `open_id` (path): TikTokユーザーのopen_id

**レスポンス例:**
```json
{
  "access_token": "act.example1234567890abcdef",
  "open_id": "user_12345"
}
```

**エラーレスポンス:**
```json
{
  "error": "No valid token found for open_id: user_12345"
}
```

## デプロイ手順

### 1. S3バケット作成
```bash
aws s3 mb s3://tiktok-token-store --region ap-northeast-1
```

### 2. Lambda関数の作成

#### 依存関係のインストール
```bash
pip install -r requirements.txt -t .
```

#### zipファイル作成
```bash
zip -r lambda-deployment.zip . -x "*.git*" "test_*" "__pycache__/*" "*.pyc"
```

#### Lambda関数作成
```bash
aws lambda create-function \
  --function-name tiktok-token-api \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT_ID:role/lambda-s3-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://lambda-deployment.zip \
  --environment Variables='{
    "TIKTOK_TOKEN_BUCKET":"tiktok-token-store",
    "TIKTOK_TOKEN_KEY":"tiktok_tokens.json"
  }'
```

### 3. API Gateway設定

#### REST API作成
```bash
aws apigateway create-rest-api --name tiktok-token-api
```

#### リソース・メソッド設定
- `/token/{open_id}` パスを作成
- GETメソッドを設定
- Lambda統合を設定

### 4. 環境変数設定

Lambda関数に以下の環境変数を設定:

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `TIKTOK_TOKEN_BUCKET` | S3バケット名 | `tiktok-token-store` |
| `TIKTOK_TOKEN_KEY` | S3オブジェクトキー | `tiktok_tokens.json` |

## IAM権限

Lambda実行ロールに以下の権限が必要:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::tiktok-token-store/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

## ローカルテスト

```bash
python test_token_store.py
```

このスクリプトでS3接続とトークン操作をテストできます。

## トラブルシューティング

### S3アクセスエラー
- AWS認証情報が正しく設定されているか確認
- IAM権限が適切に設定されているか確認
- S3バケットが存在するか確認

### Lambda実行エラー
- 環境変数が正しく設定されているか確認
- タイムアウト設定を確認（デフォルト3秒では短い場合がある）
- CloudWatch Logsでエラー詳細を確認