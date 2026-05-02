# フォーク運用・upstream 追従手順

このリポジトリは [googleads/google-ads-python](https://github.com/googleads/google-ads-python) のフォークです。
カスタム MCP 実装（FastMCP + Vercel）は `main_vercel` ブランチで管理します。

## ブランチ構成

```
main         ← upstream 追従専用（直接編集しない）
main_vercel  ← MCP サーバー実装（Vercel デプロイ対象）
```

- `main` には upstream の SDK コードのみを置く
- `main_vercel` で `api/`、`google_ads_mcp/`、`vercel.json`、`requirements.txt`、本ファイルを管理する
- `main` → `main_vercel` の自動 merge はしない。SDK 差分を確認した上で必要な変更を手で組み込む

---

## 初回セットアップ

```bash
# upstream を remote に追加
git remote add upstream https://github.com/googleads/google-ads-python.git
git fetch upstream

git remote -v
# origin    <自分のリポジトリURL>
# upstream  https://github.com/googleads/google-ads-python.git
```

---

## upstream 追従手順（定期メンテナンス）

### 1. upstream の最新を取得

```bash
git fetch upstream
```

### 2. main を upstream に追従

```bash
git checkout main
git merge upstream/main
git push origin main
```

### 3. SDK 差分を確認（手動 review）

```bash
# 例: v24 → v25 の新フィールド・リソースを確認
git diff upstream/v24.0.0..upstream/v25.0.0 -- google/ads/googleads/
```

### 4. 必要な変更を main_vercel に取り込む

差分を踏まえ、`google_ads_mcp/tools/` 配下と `api/mcp.py` の `_TOOLS` 定義を更新する。
GAQL クエリで利用しているフィールドが廃止/改名されていないかを確認する。

```bash
git checkout main_vercel
git merge main   # 必要に応じてコンフリクト解消
```

### コンフリクト方針

| ファイル | 対応方針 |
|---|---|
| `google/ads/googleads/**` | upstream の変更をそのまま採用 |
| `google_ads_mcp/**` | main_vercel 版を維持。SDK の I/F 変更があれば手動修正 |
| `api/mcp.py` | main_vercel 版を維持。新ツール追加時は `_TOOLS` と `dispatch` を編集 |
| `pyproject.toml` | upstream 版を採用（MCP 用追加依存は `requirements.txt` 側で管理） |
| `requirements.txt` | main_vercel 版を維持 |
| `vercel.json` / `UPSTREAM_SYNC.md` | main_vercel 版を維持 |

---

## 新ツールを追加するとき

1. `google_ads_mcp/tools/<file>.py` に `@mcp.tool()` 関数を実装
2. `google_ads_mcp/server.py` の import 行に追加（stdio 用の登録）
3. `api/mcp.py` の `_TOOLS` リストにスキーマを追加し、`dispatch` 辞書に関数を登録
4. ローカルで `uvicorn api.mcp:app --reload` → `tools/list` / `tools/call` で動作確認

---

## リフレッシュトークンのローテーション

Google Ads OAuth リフレッシュトークンは外部要因で失効しうるため、定期的にローテーションする。

```bash
# 1. 新しいリフレッシュトークンを発行（既存スクリプトを流用）
node scripts/generate-token.js

# 2. Vercel の環境変数を更新
vercel env rm GOOGLE_ADS_REFRESH_TOKEN production --yes
echo "<新しいトークン>" | vercel env add GOOGLE_ADS_REFRESH_TOKEN production

# 3. 再デプロイ
vercel --prod
```
