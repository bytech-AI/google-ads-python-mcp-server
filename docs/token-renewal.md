# JWT トークン更新手順書

このドキュメントでは、Google Ads MCP サーバーの JWT トークンを更新する手順を説明します。

---

## 概要

| 項目 | 値 |
|------|-----|
| トークン有効期限 | 2週間 |
| 更新頻度 | 2週間ごと（失効前に更新推奨） |
| 更新作業時間 | 約5分 |

---

## 事前準備（初回のみ）

### 1. JWT_SECRET と JWT_SALT の生成

```bash
# JWT_SECRET を生成（32バイト）
openssl rand -base64 32
# 例: K7gNU3sdo+OL0wNhqoVWhr3g6s1xYv72ol/pe/Unols=

# JWT_SALT を生成（16バイト）
openssl rand -base64 16
# 例: aB3dE5fG7hI9jK1L
```

### 2. Cloudflare Secrets に登録

```bash
# JWT_SECRET を登録
npx wrangler secret put JWT_SECRET
# プロンプトで上記の値を入力

# JWT_SALT を登録
npx wrangler secret put JWT_SALT
# プロンプトで上記の値を入力
```

### 3. ローカル用に値を保存

生成した値を安全な場所（パスワードマネージャー等）に保存してください。
トークン生成時に必要になります。

---

## 定期更新手順

### ステップ 1: トークン生成スクリプトを実行

```bash
cd /Volumes/PortableSSD/Documents/MCPServer/mcp-google-ads-remote

# 環境変数で設定して実行
JWT_SECRET="あなたのJWT_SECRET" JWT_SALT="あなたのJWT_SALT" node scripts/generate-token.js
```

または、`scripts/generate-token.js` を編集して直接値を入力してから実行：

```bash
node scripts/generate-token.js
```

### ステップ 2: 出力されたトークンをコピー

スクリプト実行後、以下のような出力が表示されます：

```
======================================================================
🔑 JWT Token Generated Successfully
======================================================================

📋 Token (以下をコピーしてください):
----------------------------------------------------------------------
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtY3AtY2xpZW50...
----------------------------------------------------------------------

📅 Token Details:
  • 発行日時: 2024/12/20 15:30:00 (JST)
  • 有効期限: 2025/01/03 15:30:00 (JST)
  • 有効期間: 2週間
  • JWT ID:   a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

### ステップ 3: Claude Desktop 設定を更新

設定ファイルを開く：

```bash
# macOS
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json

# または VSCode で開く
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

`Authorization` ヘッダーの Bearer トークンを新しい値に更新：

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "mcp-remote",
      "args": [
        "https://mcp-google-ads.s-tanaka-dcb.workers.dev/mcp",
        "--header",
        "Authorization: Bearer 新しいトークンをここに貼り付け"
      ]
    }
  }
}
```

### ステップ 4: Claude Desktop を再起動

設定を反映するため、Claude Desktop を完全に終了して再起動します。

### ステップ 5: 動作確認

Claude Desktop で Google Ads MCP ツールが使用できることを確認：

```
「list_accounts を実行して」
```

---

## Cursor の場合

### 設定ファイルの場所

```bash
# プロジェクト固有
.cursor/mcp.json

# または グローバル
~/.cursor/mcp.json
```

### 設定例

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "mcp-remote",
      "args": [
        "https://mcp-google-ads.s-tanaka-dcb.workers.dev/mcp",
        "--header",
        "Authorization: Bearer あなたのトークン"
      ]
    }
  }
}
```

---

## トラブルシューティング

### エラー: "jwt malformed" または "invalid signature"

**原因**: トークンが正しくコピーされていないか、JWT_SECRET が一致していない

**対処**:
1. トークン全体が正しくコピーされているか確認
2. `jwt.io` でトークンを検証
3. JWT_SECRET が Cloudflare Secrets と一致しているか確認

### エラー: "jwt expired"

**原因**: トークンの有効期限が切れている

**対処**:
1. 新しいトークンを生成
2. Claude Desktop 設定を更新
3. Claude Desktop を再起動

### エラー: "Unauthorized"

**原因**: Authorization ヘッダーが正しく設定されていない

**対処**:
1. `Bearer ` の後にスペースがあることを確認
2. JSON の引用符が正しいことを確認
3. 設定ファイルを保存したか確認

---

## セキュリティ注意事項

1. **JWT_SECRET は絶対に公開しない**
   - GitHub にコミットしない
   - 他人と共有しない

2. **トークンの取り扱い**
   - パスワードマネージャーで管理推奨
   - 漏洩した場合は JWT_SECRET を変更して全トークンを無効化

3. **トークン漏洩時の対応**
   ```bash
   # 新しい JWT_SECRET を生成
   openssl rand -base64 32
   
   # Secrets を更新
   npx wrangler secret put JWT_SECRET
   
   # 再デプロイ
   npm run deploy
   
   # 新しいトークンを生成
   node scripts/generate-token.js
   ```

---

## リマインダー設定（推奨）

カレンダーに2週間ごとのリマインダーを設定：

- **タイトル**: 「MCP トークン更新」
- **頻度**: 2週間ごと
- **内容**: 
  ```
  1. cd /Volumes/PortableSSD/Documents/MCPServer/mcp-google-ads-remote
  2. JWT_SECRET="xxx" JWT_SALT="xxx" node scripts/generate-token.js
  3. Claude Desktop 設定を更新
  4. Claude Desktop を再起動
  ```

---

## 更新履歴

| 日付 | 内容 |
|------|------|
| 2024-12-20 | 初版作成 |

