// ─────────────────────────────────────────────────────────────
// PHƯỚC PHIẾU — DATA (15 Phẩm Tần Số)
// Nguồn: TanSoNaCha Phước Phiếu Blueprint (OUM Studio)
// Mỗi Phẩm = 1 Phước Phiếu = 1 trang. 3 phẩm đầu đã khai mở (có board art).
// Token/QR: TD/KT/NN-[13 ký tự]-[số thứ tự]. Hệ QR = Shlink VPS.
// ─────────────────────────────────────────────────────────────

export interface Pham {
  rank: number;            // thứ tự phẩm 1..15
  slug: string;
  name: string;            // tên phẩm
  han: string;             // Hán tự
  prefix?: string;         // tiền tố mã QR (TD/KT/NN...) — chỉ phẩm đã mở
  poetic: string;          // câu thơ/ý nghĩa (trích Blueprint)
  path: 'tu-than' | 'phung-su' | 'song-dinh';
  open: boolean;           // đã khai mở chưa
  quota?: number;          // số phiếu phát hành (đợt đầu)
  cover?: string;          // ảnh board hero
  board?: string[];        // các board concept
  // màu chủ đạo theo cảm hứng phẩm (đồng bộ bảng màu Tần Số Nacha)
  hue: { from: string; to: string; accent: string; ink: string };
  glyph: string;           // biểu tượng gợi ý
}

export const PATHS: Record<string, { label: string; han: string; desc: string }> = {
  'tu-than':   { label: 'Đường Tự Thân', han: '自 身', desc: 'Gieo mà lên — Phẩm 1 đến 10, tự nâng bằng Gieo Duyên & Ấn Tống.' },
  'phung-su':  { label: 'Đường Phụng Sự', han: '奉 事', desc: 'Không mua được — Phẩm 11 đến 13, xét theo công sức và sự công nhận.' },
  'song-dinh': { label: 'Song Đỉnh', han: '雙 頂', desc: 'Hai mặt tối hậu — Phẩm 14, 15, đứng ngang nhau, không cấp nào cao hơn.' },
};

export const phamList: Pham[] = [
  {
    rank: 1, slug: 'truc-duyen', name: 'Trúc Duyên', han: '竹 緣', prefix: 'TD',
    poetic: 'Duyên mới nhú như măng tre — rỗng ruột để chứa, mềm mà không gãy.',
    path: 'tu-than', open: true, quota: 400,
    cover: '/images/phuoc-phieu/truc-duyen-board1.jpg',
    board: ['/images/phuoc-phieu/truc-duyen-board1.jpg','/images/phuoc-phieu/truc-duyen-board2.jpg','/images/phuoc-phieu/truc-duyen-board3.jpg'],
    hue: { from: '#3d5a4a', to: '#2c3a33', accent: '#B8C9C0', ink: '#eef3ef' },
    glyph: '',
  },
  {
    rank: 2, slug: 'kim-tam', name: 'Kim Tâm', han: '金 心', prefix: 'KT',
    poetic: 'Tấm lòng được tôi qua lửa — hoá vàng, hoá bền.',
    path: 'tu-than', open: true, quota: 200,
    cover: '/images/phuoc-phieu/kim-tam-board1.jpg',
    board: ['/images/phuoc-phieu/kim-tam-board1.jpg','/images/phuoc-phieu/kim-tam-board2.jpg','/images/phuoc-phieu/kim-tam-board3.jpg'],
    hue: { from: '#8B6F2E', to: '#3a2c12', accent: '#C9A96E', ink: '#F5ECD8' },
    glyph: '',
  },
  {
    rank: 3, slug: 'nguyen-niem', name: 'Nguyên Niệm', han: '元 念', prefix: 'NN',
    poetic: 'Niệm gốc — cái nghĩ đầu tiên, trước khi ly nước bị khuấy đục.',
    path: 'tu-than', open: true, quota: 100,
    cover: '/images/phuoc-phieu/nguyen-niem-board1.jpg',
    board: ['/images/phuoc-phieu/nguyen-niem-board1.jpg','/images/phuoc-phieu/nguyen-niem-board2.jpg','/images/phuoc-phieu/nguyen-niem-board3.jpg'],
    hue: { from: '#2e4b5a', to: '#16242c', accent: '#9fc4d4', ink: '#e9f2f6' },
    glyph: '',
  },
  // ── Chưa khai mở (Phẩm 4-15) ──
  { rank: 4, slug: 'phuc-co-ky', name: 'Phúc Cơ Kỳ', han: '福 基 期',
    poetic: 'Chặng đắp nền. Phước xây từ móng, không từ mái.',
    path: 'tu-than', open: false, hue: { from: '#5a4a3a', to: '#2c2620', accent: '#C9A96E', ink: '#F5F0EB' }, glyph: '' },
  { rank: 5, slug: 'thien-mong-ky', name: 'Thiên Mông Kỳ', han: '天 朦 期',
    poetic: 'Màn trời hé mở — thấy tầng cao mênh mông mà còn mờ ảo.',
    path: 'tu-than', open: false, hue: { from: '#4a4e6a', to: '#22242e', accent: '#b0b6d4', ink: '#eef0f6' }, glyph: '' },
  { rank: 6, slug: 'hop-dao-ky', name: 'Hợp Đạo Kỳ', han: '合 道 期',
    poetic: 'Hoà làm một với Đạo — con đường nào làm mình thở được.',
    path: 'tu-than', open: false, hue: { from: '#3a5a52', to: '#1c2a26', accent: '#a9c4b3', ink: '#eef3ef' }, glyph: '' },
  { rank: 7, slug: 'do-duyen-tien', name: 'Độ Duyên Tiên', han: '渡 緣 仙',
    poetic: 'Bản lề của cả thang. Thôi luyện mình, bắt đầu đưa người qua sông.',
    path: 'tu-than', open: false, hue: { from: '#6a5a2e', to: '#2e2612', accent: '#d4b47c', ink: '#F5ECD8' }, glyph: '' },
  { rank: 8, slug: 'thien-duyen-tien', name: 'Thiên Duyên Tiên', han: '天 緣 仙',
    poetic: 'Duyên được nâng lên tầm trời.',
    path: 'tu-than', open: false, hue: { from: '#4a5a7a', to: '#20262e', accent: '#b0c4d4', ink: '#eef2f6' }, glyph: '' },
  { rank: 9, slug: 'kim-duyen-tien', name: 'Kim Duyên Tiên', han: '金 緣 仙',
    poetic: 'Duyên bền như vàng — không phai theo mùa.',
    path: 'tu-than', open: false, hue: { from: '#8B6F2E', to: '#3a2c12', accent: '#e0c078', ink: '#F5ECD8' }, glyph: '' },
  { rank: 10, slug: 'dai-dao-duyen-tien', name: 'Đại Đạo Duyên Tiên', han: '大 道 緣 仙',
    poetic: 'Duyên tan vào Đại Đạo. Mốc cuối còn chạm được bằng gieo.',
    path: 'tu-than', open: false, hue: { from: '#5a4a6a', to: '#26202e', accent: '#c4b0d4', ink: '#f2eef6' }, glyph: '' },
  { rank: 11, slug: 'nhi-mong-la-han', name: 'Nhị Mông La Hán', han: '二 朦 羅 漢',
    poetic: 'Thấy tầng mờ ảo thứ hai, vượt khỏi cả thiên. Phiền não đã tận.',
    path: 'phung-su', open: false, hue: { from: '#7a3a2e', to: '#2e1612', accent: '#d49080', ink: '#F5ECE8' }, glyph: '' },
  { rank: 12, slug: 'nhat-nguyen-bo-tat', name: 'Nhất Nguyên Bồ Tát', han: '一 元 菩 薩',
    poetic: 'Giác rồi ở lại độ người. Một mà gồm tất cả.',
    path: 'phung-su', open: false, hue: { from: '#6a5a2e', to: '#2e2612', accent: '#e0c078', ink: '#F5ECD8' }, glyph: '' },
  { rank: 13, slug: 'ban-bo-phat-ton', name: 'Bán Bộ Phật Tôn', han: '半 步 佛 尊',
    poetic: 'Nửa bước tới Phật. Mãi cách đúng một bước — vì biết khiêm.',
    path: 'phung-su', open: false, hue: { from: '#8B6F2E', to: '#2e2410', accent: '#f0d890', ink: '#F8F0DC' }, glyph: '' },
  { rank: 14, slug: 'hon-nguyen-vo-dien', name: 'Hỗn Nguyên Vô Diện', han: '混 元 無 面',
    poetic: 'Cái tôi tan hết. Không mặt, không tên — về cái nguồn nguyên thuỷ trước mọi hình tướng.',
    path: 'song-dinh', open: false, hue: { from: '#2a2a2a', to: '#0e0e0e', accent: '#cfc6b0', ink: '#EDE8DC' }, glyph: '' },
  { rank: 15, slug: 'vo-cuc-hong-hoang', name: 'Vô Cực Hồng Hoang', han: '無 極 洪 荒',
    poetic: 'Cái vô cực trước khi vũ trụ thành hình. Cái kết và cái khởi nguyên là một.',
    path: 'song-dinh', open: false, hue: { from: '#3a2e4a', to: '#12101c', accent: '#c4b0e0', ink: '#F0EAF8' }, glyph: '' },
];

// ── 3 cách dùng phiếu ──
export const cachDung = [
  { key: 'gieo-duyen', han: '緣', label: 'Gieo Duyên', sub: 'Góp Quỹ',
    desc: 'Một phần giá trị vào Quỹ Gieo Duyên — in sách, bữa ăn, học bổng, thư viện. QR truy được điểm đến.' },
  { key: 'an-tong', han: '印', label: 'Ấn Tống', sub: 'Tặng Sách',
    desc: 'Dùng phiếu trao trọn một cuốn cho chùa, trường, người cần. Người mua hoá thành người phát tâm.' },
  { key: 'uu-dai', han: '惠', label: 'Ưu Đãi', sub: 'Giữ lại',
    desc: 'Giữ làm ưu đãi cho lần thỉnh sách sau. Phần thương mại rõ ràng, tách bạch khỏi phần phước.' },
];

export function getPham(slug: string): Pham | undefined {
  return phamList.find((p) => p.slug === slug);
}
export const openPhamList = () => phamList.filter((p) => p.open);
