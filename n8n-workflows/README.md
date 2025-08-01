# n8n Workflows

n8nでTikTok動画投稿を自動化するためのワークフローファイルです。

## ワークフロー一覧

### tiktok-upload.json
TikTok動画投稿の基本ワークフローです。

**機能:**
- Lambda APIからアクセストークンを取得
- TikTok APIで動画投稿を初期化
- 投稿ステータスの確認

**ノード構成:**
1. **Manual Trigger** - ワークフロー開始トリガー
2. **Set Video Data** - 投稿データの設定
3. **Get TikTok Token** - Lambda APIからトークン取得
4. **Initialize TikTok Upload** - TikTok投稿初期化
5. **Check Upload Status** - 投稿ステータス確認

## セットアップ手順

### 1. ワークフローのインポート

n8nの管理画面で以下の手順を実行:

1. **Workflows** → **Import from File** を選択
2. `tiktok-upload.json` をアップロード
3. **Import** をクリック

### 2. 設定項目の編集

#### Get TikTok Tokenノード
- **URL**: Lambda API GatewayのエンドポイントURLに変更
  ```
  https://your-api-gateway-url.amazonaws.com/token/{{$json.open_id}}
  ```

#### Set Video Dataノード
- **open_id**: 自分のTikTok open_idに変更
- **video_title**: 投稿タイトルを設定
- **video_url**: 投稿する動画のURLを設定

### 3. テスト実行

1. **Test workflow** ボタンをクリック
2. 各ノードの実行結果を確認
3. エラーがあれば設定を見直し

## 応用例

### スケジュール投稿
Manual Triggerを**Cron**ノードに変更して定期投稿:

```json
{
  "name": "Schedule",
  "type": "n8n-nodes-base.cron",
  "parameters": {
    "rule": {
      "hour": 12,
      "minute": 0
    }
  }
}
```

### 複数動画の投稿
**Split In Batches**ノードを使用して複数動画を順次投稿:

```json
{
  "name": "Split In Batches",
  "type": "n8n-nodes-base.splitInBatches",
  "parameters": {
    "batchSize": 1
  }
}
```

### Webhook経由の投稿
Manual Triggerを**Webhook**ノードに変更してAPIエンドポイント化:

```json
{
  "name": "Webhook",
  "type": "n8n-nodes-base.webhook",
  "parameters": {
    "path": "tiktok-upload",
    "httpMethod": "POST"
  }
}
```

## トラブルシューティング

### よくあるエラー

#### 401 Unauthorized
- open_idが正しく設定されているか確認
- Lambda APIのURLが正しいか確認
- TikTokトークンが有効か確認

#### 403 Forbidden
- TikTok APIの利用制限に達している可能性
- アプリケーションの権限設定を確認

#### 500 Internal Server Error
- Lambda関数が正常に動作しているか確認
- CloudWatch Logsでエラー詳細を確認

### デバッグ方法

1. **各ノードの出力を確認**
   - 実行後に各ノードをクリックして出力データを確認

2. **エラーログの確認**
   - n8nの実行履歴でエラー詳細を確認

3. **段階的テスト**
   - 各ノードを個別に実行してどこで失敗するか特定

## カスタマイズ

### 投稿設定の変更
`Initialize TikTok Upload`ノードのbodyParametersで以下を変更可能:

- **privacy_level**: `PUBLIC_TO_EVERYONE`, `MUTUAL_FOLLOW_FRIENDS`, `SELF_ONLY`
- **disable_duet**: デュエット機能の無効化
- **disable_comment**: コメント機能の無効化
- **disable_stitch**: スティッチ機能の無効化

### 動的データの利用
前のノードからのデータを参照:

```javascript
// 前のノードのデータを参照
{{$json.field_name}}

// 特定のノードのデータを参照
{{$('Node Name').item.json.field_name}}
```