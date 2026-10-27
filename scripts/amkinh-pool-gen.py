#!/usr/bin/env python3
# Sinh kho comment chung chung (không nhắc tên bài) — nhiều tone, biến thể như người thật
import sqlite3, random, re, unicodedata
random.seed()
DB='/root/.openclaw/workspace/TangKinhCac/backend/data/amkinh.db'

BASES = {
'tanthan': [  # tán thán ngắn
"Nghe mà lòng nhẹ hẳn.","Hay quá trời.","Bài này đúng gu mình.","Êm thật sự.","Nghe là thấy an.","Quá là hay.","Đúng bài mình cần hôm nay.","Nghe xong thấy khoẻ hẳn.","Tuyệt vời.","Hay không có gì để chê.","Nghe mà nổi da gà.","Bài này quý thật.","Càng nghe càng thấm.","Đỉnh thật sự.","Nghe mê luôn.","Hay tới mức phải để lại một lời.","Bấm vào không uổng.","Nghe một lần là nhớ.","Bài này chạm thật.","Cảm ơn người làm ra bài này.","Nghe mà muốn ngồi im mãi.","Ưng cái bụng.","Hay từ đầu tới cuối.","Ngọt tai lắm.","Thích cái không khí của bài này.","Vô tình bấm vào mà ở lại tới hết bài.","Đáng nghe lắm mọi người.","Nghe là ghiền.","Bài này để repeat cả ngày được.","Không ngờ hay vậy.",
],
'thienvi': [  # tĩnh tịnh thiền vị
"Tâm đang loạn nghe xong lặng hẳn.","Nam mô A Di Đà Phật.","Nghe như được ngồi bên hiên chùa.","Một hơi thở, một câu kinh, đủ an.","Càng nghe càng thấy mình nhỏ lại, an lại.","Pháp âm nhẹ như gió qua sân chùa.","Nghe xong chỉ muốn ngồi thở.","Bình an quá.","Như được rửa tâm.","Nghe mà buông được bao nhiêu chuyện.","Tâm tĩnh lại từng chút một.","Một chút tĩnh giữa ngày ồn ào.","Nghe như tiếng chuông xa.","An trú trong hơi thở, nghe trong tỉnh thức.","Lời kinh theo nhạc mà vào lòng lúc nào không hay.","Thân ở đây, tâm cũng ở đây.","Nghe bằng tai, thấm bằng tâm.","Càng vội càng nên dừng lại nghe một bài thế này.","Chậm lại một nhịp, đời dễ thở hơn.","Nghe xong thấy từ bi với mình hơn.","Như ngồi dưới tán bồ đề.","Mỗi câu là một giọt nước mát.","Tĩnh mà không vắng, lặng mà không buồn.","Nghe để nhớ mình còn một nẻo về.","Phút này đây, an lành là thật.",
],
'doithuong': [  # đời thường
"Mở cho cả nhà nghe lúc ăn cơm tối.","Nghe lúc chạy xe về quê, hợp lắm.","Tối nào cũng mở ru con ngủ.","Làm việc mở bài này đỡ căng hẳn.","Mẹ mình nghe khen êm.","Nghe lúc pha cà phê sáng, dễ chịu ghê.","Đi làm về mệt, mở lên là thấy nhẹ.","Nhà mình giờ tối nào cũng mở.","Nghe lúc tưới cây thấy vui vui.","Bà ngoại mình cũng gật gù theo.","Dọn nhà mở bài này làm hoài không mệt.","Đang ôn thi, nghe đỡ stress lắm.","Nghe trên xe buýt mà quên trạm xuống.","Cuối tuần nằm nhà nghe cả buổi.","Nấu ăn nghe cái này là chuẩn bài.","Ba mình khó tính mà cũng khen.","Con mình nghe xong ngủ ngon hơn hẳn.","Đi bộ buổi tối nghe hợp cực.","Mở trong tiệm cho khách nghe, ai cũng hỏi bài gì.","Trực đêm có bài này đỡ buồn ngủ mà lòng vẫn êm.","Ngồi may đồ nghe cả chiều.","Mưa mưa nghe cái này là hết ý.","Chăm người bệnh, nghe để vững lòng.","Sáng nào cũng mở thay chuông báo thức.",
],
'nhinho': [  # nhí nhố trẻ trung
"nghe xong auto ngủ ngon luôn á","chill dữ thần","bài này cuốn thiệt sự","ủa sao hay vậy trời","nghe mà quên deadline luôn","vibe này xin á","đỉnh của chóp","nghe muốn xỉu ngang vì êm","đưa vô playlist gấp","học bài mở cái này là chuẩn","trời ơi cái beat nó êm gì đâu","nghe chill muốn tan chảy","10 điểm không có nhưng","bài này heal dữ lắm","ai lướt ngang thì dừng lại nghe thử đi","nghiện nhẹ rồi nha","combo trà sữa + bài này = hết sảy","đang stress mà nghe cái hết luôn","bạn nào cần ngủ ngon vô đây","xin vía nghe bài này thi đậu","nghe đi rồi cảm ơn mình sau","êm hơn cả điều hoà 16 độ","cày phim mệt qua đây nghỉ tai","cái kết đẹp cho một ngày dài",
],
'quandiem': [  # nâng cao quan điểm
"Nhạc thế này mới đưa được đạo tới người trẻ.","Ai bảo nhạc Phật khô khan thì nên nghe thử.","Kết hợp truyền thống với hiện đại thế này rất đáng ủng hộ.","Âm nhạc là cửa phương tiện, bài này là ví dụ đẹp.","Giữ được cái hồn mà vẫn mới, không dễ đâu.","Đạo không xa đời, bài này chứng minh điều đó.","Người làm hiểu cả nhạc lẫn đạo mới ra được thế này.","Cân bằng giữa nghệ thuật và tâm linh rất khéo.","Hoằng pháp thời nay cần những sản phẩm thế này.","Trẻ hoá pháp âm mà không làm nhẹ pháp, hay.","Nghe được cả bằng tai người thường lẫn tâm người tu.","Không cần hiểu hết giáo lý vẫn cảm được, đó là cái giỏi.","Dòng nhạc này xứng đáng được lan rộng hơn.","Một hướng đi tử tế giữa thị trường ồn ào.","Nhạc có chánh niệm, nghe là nhận ra ngay.",
],
'nhanxet': [  # nhận xét chuyên môn chung
"Phần nền làm sạch, không đè giọng.","Mix nghe rất gọn, đeo tai nghe càng rõ.","Tiếng chuông rải khéo, không bị phô.","Giọng mộc mà tình cảm.","Nhịp chậm mà không lê thê, giữ người nghe tốt.","Bản phối tinh tế, từng lớp rõ ràng.","Âm trầm ấm, nghe đêm rất đã.","Cách xử lý khoảng lặng rất hay.","Vocal không gồng, nghe thật.","Điệp khúc lặp mà không chán, làm hay đó.","Bài được thu kỹ, không tạp âm.","Cân bằng giữa lời và nhạc chuẩn.","Đoạn dạo đầu ngắn gọn, vào bài nhanh, thích.","Không lạm dụng hiệu ứng, nghe rất sạch.","Càng nghe bằng loa xịn càng thấy chất.","Tiết chế đúng chỗ, bung đúng lúc.",
],
'hook': [  # câu hỏi mở
"Có ai nghe bài này lúc 3h sáng như mình không?","Mọi người hay nghe bài này lúc nào trong ngày?","Ai đang nghe một mình giơ tay?","Có ai vừa nghe vừa nhắm mắt như mình không?","Nghe đoạn cuối có ai nổi da gà không?","Mình nghe lần thứ mấy chục rồi, còn ai như mình?","Ai lưu bài này vô playlist rồi điểm danh coi?","Có ai nghe xong thấy nhớ nhà không?","Bài này nghe lúc mưa là đúng bài luôn, ai đồng ý?","Ai đang làm việc mà vẫn mở bài này không?","Có bạn nào cho xin thêm bài cùng kiểu này với?","Nghe cái này trước khi ngủ có ai giống mình?","Ai từ tỉnh lẻ đang nghe không, điểm danh quê cái nào?","Có ai để bài này làm nhạc chuông chưa?","Mọi người thấy đoạn nào thấm nhất?",
],
'reply': [  # câu trả lời vào hook / đồng tình
"Mình nè, đêm nào cũng vậy.","Điểm danh nha.","Y chang mình luôn.","Mình cũng thế, tưởng mỗi mình.","Đồng ý hai tay hai chân.","Chuẩn luôn bạn ơi.","Mình cũng hay nghe khung giờ đó.","Cùng team nè.","Nghe bạn nói mới để ý, đúng thật.","Mình thì thấy đoạn giữa thấm nhất.","Cảm ơn bạn nói hộ lòng mình.","Thêm một người giống bạn đây.","Hồi đầu mình cũng nghĩ vậy, giờ thì ghiền.","Bạn nói dễ thương ghê.","Mình mới lưu playlist xong.","Có mình nữa nè.","Chính xác luôn á.","Ừa nghe mưa mưa là hết bài.","Mình nghe để ngủ, hiệu quả thật.","Quê mình miền Trung, cũng đang nghe nè.",
],
}

def strip_dia(s):
    s=unicodedata.normalize('NFD',s)
    s=''.join(c for c in s if unicodedata.category(c)!='Mn').replace('đ','d').replace('Đ','D')
    return s

SUF=[""," ạ"," nha"," á"," ghê"," thiệt"," luôn"," đó"," lắm luôn"," thật sự"]
def variants(b, tone):
    out={b}
    low=b[0].lower()+b[1:]
    # bỏ dấu (chỉ tone thân mật)
    if tone in ('nhinho','reply','doithuong','tanthan'):
        out.add(strip_dia(low).rstrip('.'))
    # thêm hậu tố tự nhiên
    for _ in range(3):
        sf=random.choice(SUF)
        if sf and not b.endswith('?'):
            out.add(b.rstrip('.')+sf)
    # viết thường + bỏ chấm
    if not b.endswith('?'): out.add(low.rstrip('.'))
    return out

db=sqlite3.connect(DB)
c=db.cursor()
ins=0
for tone,arr in BASES.items():
    for b in arr:
        for v in variants(b,tone):
            v=re.sub(r'\s+',' ',v).strip()
            if len(v)<3: continue
            try:
                c.execute("insert into comment_pool(tone,body) values(?,?)",(tone,v)); ins+=1
            except sqlite3.IntegrityError: pass
db.commit()
tot=c.execute("select count(*) from comment_pool where used=0").fetchone()[0]
print(f"inserted={ins} pool_unused={tot}")
by=c.execute("select tone,count(*) from comment_pool group by tone").fetchall()
print(by)
