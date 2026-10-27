// ─────────────────────────────────────────────────────────────
// ÂM KINH — DATA (đa-artist)
// Cấu trúc: Artist → Album → Track. Thêm bài = thêm vào đây.
// Track id (dùng cho backend counter) = `${artist}:${album}:${track}`
// ─────────────────────────────────────────────────────────────

import { tieuTamGenAlbums } from './amkinh-gen';

export interface Track {
  slug: string;
  title: string;
  cn?: string;
  author?: string;
  src: string;          // đường dẫn mp3 trong /public
  cover?: string;
  duration?: string;
  tag?: string;
  ready: boolean;       // true = phát được; false = "sắp mở"
  lyrics?: { t: number; text: string }[];
}

export interface Album {
  slug: string;
  title: string;
  cn?: string;
  desc: string;
  cover?: string;
  tracks: Track[];
}

export interface Artist {
  slug: string;
  name: string;
  cn?: string;
  tagline: string;
  bio?: string;
  avatar?: string;
  albums: Album[];
}

// ── LYRICS: Dạ Nam Mô (bài mẫu hiện có) ──
const lyricsDaNamMo: { t: number; text: string }[] = [
  { t: 0.0, text: 'Dạ Nam mô Bổn Sư' },
  { t: 2.8, text: 'Thích Ca Mâu Ni Phật' },
  { t: 6.6, text: 'Dạ Nam mô Bổn Sư' },
  { t: 9.8, text: 'Thích Ca Mâu Ni Phật' },
  { t: 13.3, text: 'Nhặt một câu kinh' },
  { t: 14.9, text: 'Nhặt một chữ bình' },
  { t: 16.6, text: 'Nhặt một câu kinh' },
  { t: 18.2, text: 'Nhặt một chữ tâm' },
  { t: 19.9, text: 'Nhặt một câu kinh' },
  { t: 21.8, text: 'Nhặt một chữ bình' },
  { t: 23.7, text: 'Nhặt một chữ tâm' },
  { t: 25.6, text: 'Rơi vào tim con' },
  { t: 29.7, text: 'Đấng Đại Giác' },
  { t: 31.7, text: 'Sáng hơn sao trời' },
  { t: 35.9, text: 'Bậc Đạo Sư' },
  { t: 38.2, text: 'Của khắp muôn loài' },
  { t: 42.9, text: 'Đại Bi ôm' },
  { t: 44.8, text: 'Trọn miền pháp giới' },
  { t: 47.9, text: 'Đại Trí soi' },
  { t: 50.3, text: 'Mười phương không phai' },
  { t: 52.8, text: 'Từ vô lượng kiếp' },
  { t: 56.0, text: 'Ngài gieo phước lành' },
  { t: 59.3, text: 'Đi qua sinh tử' },
  { t: 62.5, text: 'Vì thương chúng sinh' },
  { t: 66.4, text: 'Không cầu danh vọng' },
  { t: 69.0, text: 'Không giữ riêng mình' },
  { t: 71.8, text: 'Chỉ mong muôn loài' },
  { t: 74.7, text: 'Thoát khỏi điêu linh' },
  { t: 78.8, text: 'Vì thương chúng sinh' },
  { t: 81.3, text: 'Trôi trong sinh tử' },
  { t: 84.8, text: 'Ngài rời cung vàng' },
  { t: 87.6, text: 'Bước vào rừng sâu' },
  { t: 90.5, text: 'Khoác áo ca-sa' },
  { t: 93.7, text: 'Qua miền gió bụi' },
  { t: 97.7, text: 'Tìm một con đường' },
  { t: 100.4, text: 'Chấm dứt khổ đau' },
  { t: 103.9, text: 'Dạ Nam mô Bổn Sư' },
  { t: 106.3, text: 'Thích Ca Mâu Ni Phật' },
  { t: 108.8, text: 'Om... a... ha... om...' },
  { t: 111.5, text: 'Dạ Nam mô Bổn Sư' },
  { t: 113.4, text: 'Thích Ca Mâu Ni Phật' },
  { t: 116.7, text: 'Giáng sinh Ta-bà' },
  { t: 118.3, text: 'Giữa đời mộng huyễn' },
  { t: 119.8, text: 'Làm bậc Thái tử' },
  { t: 121.5, text: 'Đầy đủ vinh hoa' },
  { t: 123.2, text: 'Nhưng nhìn thế gian' },
  { t: 124.7, text: 'Vô thường tan biến' },
  { t: 126.1, text: 'Ngài bỏ cung vàng' },
  { t: 127.9, text: 'Tìm lối vượt qua' },
  { t: 130.1, text: 'Trong rừng sâu vắng' },
  { t: 133.1, text: 'Dưới trời sao mai' },
  { t: 137.0, text: 'Ngài ngồi bất động' },
  { t: 139.5, text: 'Tâm không đổi thay' },
  { t: 142.0, text: 'Ma chướng tan rã' },
  { t: 145.4, text: 'Đêm dài mở sáng' },
  { t: 148.8, text: 'Vô Thượng Chánh Giác' },
  { t: 151.7, text: 'Bừng khắp mười phương' },
  { t: 154.7, text: 'Vì thương chúng sinh' },
  { t: 157.8, text: 'Trôi trong sinh tử' },
  { t: 161.7, text: 'Ngài rời cung vàng' },
  { t: 164.5, text: 'Bước vào rừng sâu' },
  { t: 167.4, text: 'Khoác áo ca-sa' },
  { t: 170.6, text: 'Qua miền gió bụi' },
  { t: 173.8, text: 'Tìm một con đường' },
  { t: 176.9, text: 'Chấm dứt khổ đau' },
  { t: 179.9, text: 'Ngài đi vì thương' },
  { t: 183.3, text: 'Ngài sáng vì thương' },
  { t: 186.6, text: 'Ngài gọi muôn loài' },
  { t: 189.7, text: 'Trở về tỉnh thức' },
  { t: 192.8, text: 'Dạ Nam mô Bổn Sư' },
  { t: 195.6, text: 'Thích Ca Mâu Ni Phật' },
  { t: 199.6, text: 'Dạ Nam mô Bổn Sư' },
  { t: 202.2, text: 'Thích Ca Mâu Ni Phật' },
  { t: 205.8, text: 'Giới Ngài thanh tịnh' },
  { t: 207.6, text: 'Như trời không mây' },
  { t: 209.4, text: 'Định Ngài vững chãi' },
  { t: 211.1, text: 'Như núi Tu-di' },
  { t: 212.7, text: 'Trí Ngài sâu rộng' },
  { t: 214.3, text: 'Như biển không bờ' },
  { t: 215.8, text: 'Từ Bi của Ngài' },
  { t: 217.8, text: 'Che khắp bến mê' },
  { t: 219.8, text: 'Xin cho ánh sáng' },
  { t: 222.6, text: 'Chánh Pháp còn mãi' },
  { t: 225.5, text: 'Soi khắp thế gian' },
  { t: 228.7, text: 'Đang nhiều thương đau' },
  { t: 231.9, text: 'Xin cho chiến tranh' },
  { t: 235.1, text: 'Hận thù lắng xuống' },
  { t: 238.4, text: 'Muôn loài nhìn nhau' },
  { t: 241.4, text: 'Bằng mắt nhiệm màu' },
  { t: 245.0, text: 'Vì thương chúng sinh' },
  { t: 247.7, text: 'Trôi trong sinh tử' },
  { t: 251.3, text: 'Ngài rời cung vàng' },
  { t: 254.0, text: 'Bước vào rừng sâu' },
  { t: 257.6, text: 'Khoác áo ca-sa' },
  { t: 260.5, text: 'Qua miền gió bụi' },
  { t: 263.4, text: 'Tìm một con đường' },
  { t: 266.6, text: 'Chấm dứt khổ đau' },
  { t: 269.7, text: 'Dạ Nam mô Bổn Sư' },
  { t: 272.6, text: 'Thích Ca Mâu Ni Phật' },
  { t: 275.4, text: 'Ánh sáng Như Lai' },
  { t: 277.0, text: 'Soi vào tâm con' },
  { t: 278.6, text: 'Dạ Nam mô Bổn Sư' },
  { t: 282.4, text: 'Thích Ca Mâu Ni Phật' },
  { t: 285.9, text: 'Nguyện khắp muôn loài' },
  { t: 289.6, text: 'Đồng thành Phật đạo' },
  { t: 293.1, text: 'Nhặt một câu kinh' },
  { t: 294.2, text: 'Nhặt một chữ bình' },
  { t: 295.8, text: 'Nhặt một câu kinh' },
  { t: 297.5, text: 'Nhặt một chữ tâm' },
  { t: 299.0, text: 'Nhặt một câu kinh' },
  { t: 300.6, text: 'Nhặt một chữ bình' },
  { t: 302.2, text: 'Nhặt một chữ tâm' },
  { t: 304.7, text: 'Rơi vào tim con' },
  { t: 308.6, text: 'Nhặt một câu kinh' },
  { t: 312.6, text: 'Nhặt một chữ tâm' },
  { t: 316.6, text: 'Rơi vào tim con...' },
];

// ═══════════════════════════════════════════════════════════════
// ARTISTS — hiện tại: Tiểu Tâm. Sau này thêm artist/tác giả khác vào mảng này.
// ═══════════════════════════════════════════════════════════════
export const artists: Artist[] = [
  {
    slug: 'tieu-tam',
    name: 'Tiểu Tâm',
    cn: '小 心',
    tagline: 'Nơi lời Phật hoá thành thanh âm.',
    bio: 'Tiểu Tâm — người gom nhặt lời kinh, dệt thành Âm Kinh. Mỗi bài là một mảnh chuyện Như Lai, một hơi thở tỉnh thức.',
    avatar: '/images/art/nacha-tiger.jpg',
    albums: [
      {
        slug: 'already-phat',
        title: 'Already Phật',
        cn: '不 空',
        desc: 'Album riêng — Tác giả: Bất Không Already Phật · Ca sỹ: Tiểu Tâm. Bài khai môn của Âm Kinh.',
        cover: '/images/art/nacha-tiger.jpg',
        tracks: [
          {
            slug: 'da-nam-mo',
            title: 'Dạ Nam Mô Bổn Sư Thích Ca Mâu Ni Phật',
            cn: '本 師 釋 迦',
            author: 'Bất Không Already Phật',
            src: '/audio/da-nam-mo-bon-su-thich-ca-mau-ni-phat.mp3',
            cover: '/images/art/nacha-tiger.jpg',
            duration: '5:23',
            tag: 'Lofi · Chill',
            ready: true,
            lyrics: lyricsDaNamMo,
          },
        ],
      },
      {
        slug: 'da-nacha',
        title: 'Dạ Nacha',
        cn: '那 迦',
        desc: 'Lofi kể chuyện Như Lai — 108 mảnh chuyện, nhịp trầm, kinh văn thì thầm.',
        cover: '/images/art/nacha-tiger.jpg',
        tracks: [],
      },
      {
        slug: 'da-sifu-minh-tue',
        title: 'Dą Sifu Minh Tuệ',
        cn: '明 慧',
        desc: 'Hành trạng, buông bỏ, khất thực, thiểu dục tri túc — mạch Thầy Minh Tuệ.',
        cover: '/images/art/img-07-wide.jpg',
        tracks: [],
      },
      {
        slug: 'da-vo-dien-phat',
        title: 'Dạ Vô Diện Phật',
        cn: '無 面 佛',
        desc: 'Thiền định, vô tướng — Phật không mặt, khắp muôn nơi.',
        cover: '/images/art/img-18-wide.jpg',
        tracks: [],
      },
    ],
  },
];



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

// ── Helpers ──
export function trackId(artistSlug: string, albumSlug: string, trackSlug: string): string {
  return `${artistSlug}:${albumSlug}:${trackSlug}`;
}

export function getArtist(slug: string): Artist | undefined {
  return artists.find((a) => a.slug === slug);
}

export function getAlbum(artistSlug: string, albumSlug: string): { artist: Artist; album: Album } | undefined {
  const artist = getArtist(artistSlug);
  const album = artist?.albums.find((al) => al.slug === albumSlug);
  if (artist && album) return { artist, album };
  return undefined;
}

export function getTrack(artistSlug: string, albumSlug: string, trackSlug: string) {
  const res = getAlbum(artistSlug, albumSlug);
  const track = res?.album.tracks.find((t) => t.slug === trackSlug);
  if (res && track) return { artist: res.artist, album: res.album, track };
  return undefined;
}

export function albumTrackCount(album: Album): number {
  return album.tracks.length;
}
export function albumReadyCount(album: Album): number {
  return album.tracks.filter((t) => t.ready).length;
}
