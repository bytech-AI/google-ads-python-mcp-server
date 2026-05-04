# Vercel リモート MCP デプロイ手順（振り返り）

このリポジトリ（`google-ads-python-mcp-server`）を Vercel 上にリモート MCP サーバーとして公開する手順を、実際の作業順にまとめる。社内利用・Vercel Pro 個人プラン・MCC 配下複数アカウント運用を前提とする。

---

## 全体像

```
[Claude Desktop / Cursor]
        │ Authorization: Bearer <MCP_AUTH_TOKEN>
        ▼
[Vercel Function (api/mcp.py)]
        │ refresh_token → access_token
        ▼
[Google Ads API]
```

- **入口認証**: `MCP_AUTH_TOKEN`（自前発行の JWT 形式トークン、文字列一致で検証）
- **API認証**: `GOOGLE_ADS_*` 一式（OAuth 2.0 リフレッシュトークン）
- **デプロイ単位**: `api/mcp.py` を Vercel Python Function として公開

---

## 前提条件

| 項目 | 内容 |
|---|---|
| Google Ads | Developer Token 取得済み（Standard 推奨） |
| OAuth | Client ID / Client Secret / Refresh Token 取得済み |
| MCC | ログイン顧客 ID（10桁ハイフン無し）を把握 |
| OAuth 同意画面 | "In production" または "Internal"（"Testing" だと7日で失効） |
| Vercel | Pro 個人プラン契約・GitHub 連携済み |
| ローカル環境 | Node.js（トークン生成スクリプト用）、`gh` CLI |

---

## ステップ 1: シークレット管理ファイルの整備

### 1-1. `.gitignore` に env 系を追加

```
.env
.env.*
!.env.example
google-ads.yaml
google_ads_token.json
.vercel
```

### 1-2. `.vercelignore` を作成

デプロイバンドルから secrets / tests を除外。

```
.env
.env.*
!.env.example
google-ads.yaml
動作確認手順.md
tests/
examples/
.venv/
__pycache__/
*.pyc
.git/
.github/
```

### 1-3. `.env.example`（コミット可）と `.env.local`（git無視）を作成

`.env.local` は `export KEY=...` 形式で `source` できるようにする。

```bash
# .env.local の中身
export GOOGLE_ADS_DEVELOPER_TOKEN=""
export GOOGLE_ADS_CLIENT_ID=""
export GOOGLE_ADS_CLIENT_SECRET=""
export GOOGLE_ADS_REFRESH_TOKEN=""
export GOOGLE_ADS_LOGIN_CUSTOMER_ID=""
export MCP_AUTH_TOKEN=""
```

---

## ステップ 2: MCP_AUTH_TOKEN の発行

クライアント（Claude Desktop 等）→ Vercel の入口認証用トークンを JWT 形式で発行する。

### 2-1. JWT_SECRET / JWT_SALT を生成

```bash
openssl rand -base64 32   # JWT_SECRET
openssl rand -base64 16   # JWT_SALT
```

両方とも安全な場所（パスワードマネージャ）に保管。2週間ごとのトークン再発行で再利用する。

### 2-2. トークン生成スクリプトを実行

`scripts/generate-token.js` を実行すると、JWT を発行して `.env.local` の `MCP_AUTH_TOKEN` を自動更新する。

```bash
JWT_SECRET="<32バイト>" JWT_SALT="<16バイト>" node scripts/generate-token.js
```

**注意**: 現在のサーバー実装（[api/mcp.py](../api/mcp.py)）は JWT を **opaque な文字列として完全一致比較** しているだけで、署名検証や `exp` チェックは行っていない。長くてランダムな共有秘密として運用し、2週間ごとに手動ローテーションする。

---

## ステップ 3: Google Ads OAuth リフレッシュトークン

### 3-1. 認可 URL にアクセスして `code` を取得

```
https://accounts.google.com/o/oauth2/auth?client_id=<CLIENT_ID>&redirect_uri=http://localhost&scope=https://www.googleapis.com/auth/adwords&access_type=offline&response_type=code
```

Google で承認 → `http://localhost/?code=...` にリダイレクトされる。`code=` の値をコピー。

### 3-2. `code` を refresh_token に交換

```bash
curl -X POST https://oauth2.googleapis.com/token \
  -d "code=<CODE>" \
  -d "client_id=<CLIENT_ID>" \
  -d "client_secret=<CLIENT_SECRET>" \
  -d "redirect_uri=http://localhost" \
  -d "grant_type=authorization_code"
```

レスポンスの `refresh_token` を `.env.local` の `GOOGLE_ADS_REFRESH_TOKEN` に設定。

### 3-3. リフレッシュトークンの寿命

- 明示的な期限はないが、以下で失効する:
  - **6ヶ月使われない**
  - **OAuth 同意画面が "Testing" → 7日で失効**
  - 同一 client_id × user で 50個超
  - ユーザーがアクセス権を取り消し
  - client_secret のローテーション

詳細は [リフレッシュトークンのみ更新する手順.md](../リフレッシュトークンのみ更新する手順.md)。

---

## ステップ 4: Vercel プロジェクトの設定

### 4-1. プロジェクト作成

GitHub リポジトリを Vercel にインポート（ダッシュボードから操作）。

### 4-2. Production Branch を設定

**Settings → Git → Production Branch** を `main_vercel` に変更（このリポジトリは upstream `google-ads-python` のフォークで、`main` は upstream 追従用に温存しているため）。

### 4-3. Environment Variables を Production に登録

**Settings → Environment Variables** で以下6つを **Production** スコープで登録:

| Key | 値の出処 |
|---|---|
| `GOOGLE_ADS_DEVELOPER_TOKEN` | Google Ads アカウント |
| `GOOGLE_ADS_CLIENT_ID` | OAuth クライアント |
| `GOOGLE_ADS_CLIENT_SECRET` | OAuth クライアント |
| `GOOGLE_ADS_REFRESH_TOKEN` | ステップ3で取得 |
| `GOOGLE_ADS_LOGIN_CUSTOMER_ID` | MCC の10桁 |
| `MCP_AUTH_TOKEN` | ステップ2で発行 |

---

## ステップ 5: ビルド設定の落とし穴対応

### 5-1. `api/requirements.txt` を必ず置く

ルートに upstream 由来の `pyproject.toml`（`name = "google-ads"`）があると、Vercel Python builder がこれを優先し、ルートの `requirements.txt` を **無視する**。結果として:

```
ModuleNotFoundError: No module named 'fastapi'
```

が発生する。

**対処**: Function ファイル（`api/mcp.py`）と同じディレクトリに `api/requirements.txt` を配置すれば、その Function 用に最優先で読まれる。

```
# api/requirements.txt
google-ads>=24.0.0
mcp>=1.24.0
fastapi>=0.115.0
uvicorn>=0.34.0
httpx>=0.28.1
```

### 5-2. `vercel.json`

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/mcp.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "15mb",
        "runtime": "python3.11"
      }
    }
  ],
  "routes": [
    { "src": "/(.*)", "dest": "api/mcp.py" }
  ]
}
```

---

## ステップ 6: デプロイと疎通確認

### 6-1. デプロイ

`main_vercel` への push、またはダッシュボードから **Redeploy（Use existing Build Cache 無効）** で実行。

### 6-2. ビルドログのチェックポイント

- `Collecting fastapi` が出ていること
- `Collecting google-ads` が出ていること
- `Using cached runtime dependencies` だけで終わっていないこと（古いキャッシュが残っているサイン）

### 6-3. 疎通確認

```bash
PROD_URL="https://<your-deployment>.vercel.app"
source .env.local

# health
curl -s "$PROD_URL/health" | jq

# tools/list
curl -s -X POST "$PROD_URL/mcp" \
  -H "Authorization: Bearer $MCP_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | jq '.result.tools[].name'

# 認証なしで 401 が返ること
curl -s -o /dev/null -w "%{http_code}\n" -X POST "$PROD_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

期待値:
- `/health` → `{"status":"healthy", "google_ads_auth_ok": true, "mcp_auth_configured": true}`
- `tools/list` → 9件のツール名
- 認証なし → `401`

---

## ステップ 7: Claude Desktop への登録

`~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "google-ads": {
      "type": "http",
      "url": "https://<your-deployment>.vercel.app/mcp",
      "headers": {
        "Authorization": "Bearer <MCP_AUTH_TOKENの実値>"
      }
    }
  }
}
```

`type: "http"` 非対応のバージョンでは `mcp-remote` 経由:

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://<your-deployment>.vercel.app/mcp",
        "--header",
        "Authorization: Bearer <MCP_AUTH_TOKENの実値>"
      ]
    }
  }
}
```

Claude Desktop を完全終了 → 再起動。ツール一覧に9件並べば完了。

---

## 実作業で詰まった点（教訓）

| 詰まりポイント | 原因 | 対処 |
|---|---|---|
| `ModuleNotFoundError: fastapi` | ルート pyproject.toml が requirements.txt より優先 | `api/requirements.txt` を追加 |
| `Using cached runtime dependencies` のまま | ビルドキャッシュが古い | Redeploy 時に「Use existing Build Cache」のチェックを外す |
| Production env が反映されない | Production Branch が `main` のままで `main_vercel` への push が Preview 扱い | Settings → Git で Production Branch を `main_vercel` に変更 |
| Vercel CLI でログインできない | ローカル環境制約 | ダッシュボード経由で env 登録・Redeploy |

---

## 定期メンテナンス

| 作業 | 頻度 | 手順 |
|---|---|---|
| `MCP_AUTH_TOKEN` ローテーション | 2週間 | `node scripts/generate-token.js` → Vercel env 更新 → 再デプロイ → クライアント設定更新 |
| `GOOGLE_ADS_REFRESH_TOKEN` 更新 | 失効時のみ | [リフレッシュトークンのみ更新する手順.md](../リフレッシュトークンのみ更新する手順.md) |
| upstream 同期 | 必要時 | [UPSTREAM_SYNC.md](../UPSTREAM_SYNC.md) に従い `main` を更新 → `main_vercel` にマージ |

---

## 関連ドキュメント

- [動作確認手順.md](../動作確認手順.md) — ローカル含む詳細な動作確認手順
- [docs/token-renewal.md](token-renewal.md) — JWT トークン更新詳細（Cloudflare 版ベース。Vercel 用に要読み替え）
- [リフレッシュトークンのみ更新する手順.md](../リフレッシュトークンのみ更新する手順.md) — Google OAuth refresh token 再発行
- [docs/gaql-google-ads-query-language.md](gaql-google-ads-query-language.md) — GAQL リファレンス
- [docs/great-gaql-samples.md](great-gaql-samples.md) — GAQL サンプル集
