#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# MERGE amkinh-tieutam.gen.json → website/src/data/amkinh-gen.ts
# + vá amkinh.ts để artist tieu-tam dùng albums merge.
# Quy tắc: da-nacha gộp (bài gốc da-nam-mo đứng đầu, giữ lyrics gốc);
# da-sifu-minh-tue + da-vo-dien-phat thay tracks rỗng; album khác append.
# ─────────────────────────────────────────────────────────────
import json, os, re

WS = '/root/.openclaw/workspace/TangKinhCac/website/src/data'
gen = json.load(open(f'{WS}/amkinh-tieutam.gen.json'))

def ts_str(s):
    return json.dumps(s, ensure_ascii=False)

def track_ts(t, indent='      '):
    parts = [f"slug: {ts_str(t['slug'])}", f"title: {ts_str(t['title'])}", "author: 'Tiểu Tâm'",
             f"src: {ts_str(t['src'])}"]
    if t.get('cover'): parts.append(f"cover: {ts_str(t['cover'])}")
    if t.get('duration'): parts.append(f"duration: {ts_str(t['duration'])}")
    if t.get('tag'): parts.append(f"tag: {ts_str(t['tag'])}")
    parts.append('ready: true')
    out = indent + '{ ' + ', '.join(parts)
    lyr = t.get('lyrics')
    if lyr:
        lj = ', '.join('{ t: %s, text: %s }' % (l['t'], ts_str(l['text'])) for l in lyr)
        out += f', lyrics: [{lj}]'
    out += ' },'
    return out

lines = ["// ĐƯỢC SINH TỰ ĐỘNG bởi scripts/merge-amkinh.py — ĐỪNG SỬA TAY.",
         "// Nguồn: amkinh-tieutam.gen.json (307 bài, 3 kho, artist Tiểu Tâm).",
         "import type { Album } from './amkinh';", '',
         'export const tieuTamGenAlbums: Album[] = [']
for a in gen['albums']:
    lines.append('  {')
    lines.append(f"    slug: {ts_str(a['slug'])},")
    lines.append(f"    title: {ts_str(a['title'])},")
    if a.get('cn'): lines.append(f"    cn: {ts_str(a['cn'])},")
    lines.append(f"    desc: {ts_str(a['desc'])},")
    cover = a.get('cover') or (a['tracks'][0].get('cover') if a['tracks'] else None)
    if cover: lines.append(f"    cover: {ts_str(cover)},")
    lines.append('    tracks: [')
    for t in a['tracks']:
        lines.append(track_ts(t))
    lines.append('    ],')
    lines.append('  },')
lines.append('];')
open(f'{WS}/amkinh-gen.ts','w').write('\n'.join(lines) + '\n')
print('amkinh-gen.ts written:', len(gen['albums']), 'albums,', sum(len(a['tracks']) for a in gen['albums']), 'tracks')

# ── vá amkinh.ts ──
src = open(f'{WS}/amkinh.ts').read()
if 'tieuTamGenAlbums' in src:
    print('amkinh.ts already patched'); raise SystemExit

# 1. import (đặt sau dòng đầu comment block — chèn trước interface Track)
src = src.replace("export interface Track {",
"""import { tieuTamGenAlbums } from './amkinh-gen';

export interface Track {""", 1)

# 2. merge logic sau mảng artists
merge_code = """

// ── MERGE ALBUM SINH TỰ ĐỘNG (307 bài từ 3 kho — artist Tiểu Tâm) ──
// da-nacha: gộp, bài gốc giữ nguyên đứng đầu; album trùng slug: thay tracks rỗng; còn lại: append.
(function mergeGen() {
  const tt = artists.find((a) => a.slug === 'tieu-tam');
  if (!tt) return;
  for (const gal of tieuTamGenAlbums) {
    const cur = tt.albums.find((al) => al.slug === gal.slug);
    if (!cur) { tt.albums.push(gal); continue; }
    const have = new Set(cur.tracks.map((t) => t.slug));
    // giữ desc/cover gốc nếu có, bổ sung cover từ gen nếu thiếu
    if (!cur.cover && gal.cover) cur.cover = gal.cover;
    for (const t of gal.tracks) {
      if (!have.has(t.slug)) cur.tracks.push(t);
    }
  }
})();
"""
marker = "// ── Helpers ──"
assert marker in src, 'marker not found'
src = src.replace(marker, merge_code + '\n' + marker, 1)
open(f'{WS}/amkinh.ts','w').write(src)
print('amkinh.ts patched')
