// ─────────────────────────────────────────────────────────────
// SINH PHƯỚC PHIẾU HÀNG LOẠT
// Mỗi phiếu: 1 mã TD/KT/NN-[13]-[seq] → voucher DB + Shlink short-url + QR PNG
// Chạy: node --experimental-sqlite gen-vouchers.mjs
// ─────────────────────────────────────────────────────────────
import { DatabaseSync } from 'node:sqlite';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { mkdirSync } from 'node:fs';
import { randomBytes } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import fsSync from 'node:fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const db = new DatabaseSync(join(__dirname, 'data', 'phuocphieu.db'));

const SHLINK = 'https://qr.62.146.238.213.sslip.io';
const KEY = '1a4081c8-feb1-44a9-b6ae-f67b88ab1a55';
const SITE = 'https://tangkinhcac.62.146.238.213.sslip.io';

const BATCHES = [
  { prefix: 'TD', pham: 'truc-duyen', name: 'Trúc Duyên', qty: 400 },
  { prefix: 'KT', pham: 'kim-tam',    name: 'Kim Tâm',    qty: 200 },
  { prefix: 'NN', pham: 'nguyen-niem',name: 'Nguyên Niệm',qty: 100 },
];

const ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
function gen13() {
  const b = randomBytes(13); let s = '';
  for (let i = 0; i < 13; i++) s += ALPHABET[b[i] % ALPHABET.length];
  return s;
}

const insV = db.prepare('INSERT OR IGNORE INTO vouchers (code,pham,prefix,seq,status,created) VALUES (?,?,?,?,?,?)');
const existsCode = db.prepare('SELECT 1 FROM vouchers WHERE code=?');
const existsSeq = db.prepare('SELECT code FROM vouchers WHERE prefix=? AND seq=?');

async function shlinkCreate(code, pham) {
  // customSlug = code; longUrl = SITE/pp/<code>
  const body = JSON.stringify({
    longUrl: `${SITE}/pp/${code}`,
    customSlug: code,
    tags: ['phuoc-phieu', pham],
    title: `Phước Phiếu ${code}`,
    findIfExists: true,
  });
  try {
    const out = execFileSync('curl', ['-s', '-m', '15', '-X', 'POST', `${SHLINK}/rest/v3/short-urls`,
      '-H', `X-Api-Key: ${KEY}`, '-H', 'Content-Type: application/json', '-d', body], { encoding: 'utf8' });
    return out.includes('"shortUrl"');
  } catch { return false; }
}

async function main() {
  const outDir = join(__dirname, 'vouchers-out');
  mkdirSync(outDir, { recursive: true });
  const manifest = [];
  const now = Date.now();

  for (const bt of BATCHES) {
    const dir = join(outDir, bt.pham);
    mkdirSync(dir, { recursive: true });
    console.log(`\n=== ${bt.name} (${bt.qty}) ===`);
    for (let seq = 1; seq <= bt.qty; seq++) {
      // RESUME: nếu seq này đã có → dùng lại code cũ, đảm bảo shlink+qr tồn tại
      const existing = existsSeq.get(bt.prefix, seq);
      let code, isNew = false;
      if (existing) { code = existing.code; }
      else {
        do { code = `${bt.prefix}-${gen13()}-${String(seq).padStart(4, '0')}`; } while (existsCode.get(code));
        insV.run(code, bt.pham, bt.prefix, seq, 'new', now);
        isNew = true;
      }
      const shortUrl = `${SHLINK}/${code}`;
      const png = join(dir, `${code}.png`);
      let ok = true;
      // chỉ gọi Shlink cho voucher MỚI (voucher cũ đã có short-url rồi)
      if (isNew) ok = await shlinkCreate(code, bt.pham);
      // QR PNG: chỉ sinh nếu chưa có
      if (!fsSync.existsSync(png)) execFileSync('qrencode', ['-o', png, '-s', '8', '-m', '2', '-l', 'M', shortUrl]);
      manifest.push({ code, pham: bt.pham, seq, shortUrl, shlink: ok });
      if (seq % 25 === 0) { console.log(`  ...${bt.prefix} ${seq}/${bt.qty}`); }
    }
    console.log(`  ✓ ${bt.name}: ${bt.qty} phiếu`);
  }

  // ghi manifest CSV
  const csv = 'code,pham,seq,shortUrl\n' + manifest.map((m) => `${m.code},${m.pham},${m.seq},${m.shortUrl}`).join('\n');
  const fs = await import('node:fs');
  fs.writeFileSync(join(outDir, 'manifest.csv'), csv);
  console.log(`\n✅ TỔNG: ${manifest.length} phiếu · manifest.csv · QR PNG trong vouchers-out/<pham>/`);
}
main();
