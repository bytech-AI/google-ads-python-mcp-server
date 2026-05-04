#!/usr/bin/env node

/**
 * MCP Auth Token Generator for Google Ads MCP Server
 *
 * 使い方:
 *   JWT_SECRET="..." JWT_SALT="..." node scripts/generate-token.js
 *
 * 初回の鍵生成:
 *   openssl rand -base64 32  # JWT_SECRET
 *   openssl rand -base64 16  # JWT_SALT
 *
 * 有効期限: 2週間
 *
 * 注意:
 *   現在の api/mcp.py は MCP_AUTH_TOKEN を opaque な文字列として完全一致比較する。
 *   このスクリプトが発行する JWT 文字列をそのまま MCP_AUTH_TOKEN に格納し、
 *   2週間ごとにローテーションする運用を想定している。
 *   サーバー側で JWT 検証（exp / 署名）を行う場合は別途 _is_authorized を改修すること。
 */

import crypto from 'crypto';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ENV_LOCAL = path.resolve(__dirname, '../.env.local');

// ============================================
// 設定
// ============================================

const JWT_SECRET = process.env.JWT_SECRET || '';
const JWT_SALT = process.env.JWT_SALT || '';

if (!JWT_SECRET || !JWT_SALT) {
  console.error('\n❌ エラー: JWT_SECRET と JWT_SALT を環境変数で設定してください\n');
  console.log('秘密鍵の生成コマンド:');
  console.log('  openssl rand -base64 32  # JWT_SECRET');
  console.log('  openssl rand -base64 16  # JWT_SALT\n');
  console.log('実行例:');
  console.log('  JWT_SECRET="..." JWT_SALT="..." node scripts/generate-token.js\n');
  process.exit(1);
}

// ============================================
// JWT 生成
// ============================================

const TWO_WEEKS = 60 * 60 * 24 * 14;
const now = Math.floor(Date.now() / 1000);

const header = { alg: 'HS256', typ: 'JWT' };
const payload = {
  sub: 'google-ads-mcp-client',
  iat: now,
  exp: now + TWO_WEEKS,
  salt: JWT_SALT,
  jti: crypto.randomUUID(),
};

function base64url(obj) {
  return Buffer.from(JSON.stringify(obj))
    .toString('base64')
    .replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
}

const headerB64 = base64url(header);
const payloadB64 = base64url(payload);
const message = `${headerB64}.${payloadB64}`;

const signature = crypto
  .createHmac('sha256', JWT_SECRET)
  .update(message)
  .digest('base64')
  .replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');

const token = `${message}.${signature}`;

// ============================================
// .env.local 自動更新（export 形式）
// ============================================

if (fs.existsSync(ENV_LOCAL)) {
  let content = fs.readFileSync(ENV_LOCAL, 'utf-8');
  const line = `export MCP_AUTH_TOKEN="${token}"`;
  if (/^\s*export\s+MCP_AUTH_TOKEN=.*/m.test(content)) {
    content = content.replace(/^\s*export\s+MCP_AUTH_TOKEN=.*/m, line);
  } else if (/^\s*MCP_AUTH_TOKEN=.*/m.test(content)) {
    content = content.replace(/^\s*MCP_AUTH_TOKEN=.*/m, line);
  } else {
    content += `\n${line}\n`;
  }
  fs.writeFileSync(ENV_LOCAL, content);
  console.log('\n✅ .env.local の MCP_AUTH_TOKEN を更新しました');
  console.log('   反映するにはシェルで `source .env.local` を再実行してください');
}

// ============================================
// 出力
// ============================================

const issuedDate = new Date(payload.iat * 1000);
const expiryDate = new Date(payload.exp * 1000);
const toJST = (d) => d.toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' });

console.log('\n' + '='.repeat(70));
console.log('🔑 MCP Auth Token Generated Successfully');
console.log('='.repeat(70));

console.log('\n📋 Token (以下をコピーしてください):');
console.log('-'.repeat(70));
console.log(token);
console.log('-'.repeat(70));

console.log('\n📅 Token Details:');
console.log(`  • 発行日時: ${toJST(issuedDate)} (JST)`);
console.log(`  • 有効期限: ${toJST(expiryDate)} (JST)`);
console.log(`  • 有効期間: 2週間`);
console.log(`  • JWT ID:   ${payload.jti}`);

console.log('\n📝 Vercel 環境変数への登録:');
console.log('-'.repeat(70));
console.log('  printf "%s" "<上記トークン>" | vercel env add MCP_AUTH_TOKEN production');
console.log('  vercel --prod  # 再デプロイで反映');
console.log('-'.repeat(70));

console.log('\n📝 Claude Desktop 設定例 (~/Library/Application Support/Claude/claude_desktop_config.json):');
console.log('-'.repeat(70));
console.log(JSON.stringify({
  mcpServers: {
    'google-ads': {
      type: 'http',
      url: 'https://<your-deployment>.vercel.app/mcp',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  },
}, null, 2));
console.log('-'.repeat(70));

console.log('\n⚠️  注意事項:');
console.log('  • このトークンは2週間後に失効します（運用上のローテーション目安）');
console.log('  • 失効前に再度このスクリプトを実行して MCP_AUTH_TOKEN を更新してください');
console.log('  • JWT_SECRET / JWT_SALT は外部に漏らさず、ローテーション用の鍵として保管してください');
console.log('  • Vercel 側の MCP_AUTH_TOKEN も忘れず更新（vercel env rm → add → 再デプロイ）');
console.log('\n' + '='.repeat(70) + '\n');

if (process.argv.includes('--token-only')) {
  process.stdout.write(token + '\n');
}
