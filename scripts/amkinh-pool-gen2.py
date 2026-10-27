#!/usr/bin/env python3
# Mở rộng kho comment lên ~6k: thêm base mới + biến thể tự nhiên (prefix/suffix/bỏ dấu/emoji nhẹ)
import sqlite3, random, re, unicodedata
random.seed(20260711)
DB='/root/.openclaw/workspace/TangKinhCac/backend/data/amkinh.db'

MORE = {
'tanthan': ["Bài này nghe một lần là ưng.","Giai điệu đi vào lòng người.","Nghe mà thấy biết ơn.","Không phí một giây nào.","Bấm vô nghe thử mà ở lại tới cuối.","Hay hơn mình nghĩ nhiều.","Nghe xong phải quay lại bấm thích.","Một bài đáng để chia sẻ.","Càng về sau càng hay.","Chỗ này đúng là kho báu.","Nghe lần hai vẫn nguyên cảm xúc.","Bài nào ở đây cũng chất lượng.","Người làm bài này có tâm thật.","Xứng đáng nhiều người biết tới hơn.","Nghe mà thấy lòng biết ơn vô cùng.","Không uổng công tìm tới đây.","Mỗi lần nghe là một lần mới.","Đúng chất, không lẫn đi đâu được.","Nghe là muốn giới thiệu cho bạn bè.","Từng giai điệu đều có hồn."],
'thienvi': ["Nghe mà thấy vô thường nhẹ tênh.","Một niệm buông, ngàn mối gỡ.","Tâm an thì cảnh an, nghe bài này thấy rõ.","Như được ngồi lại với chính mình.","Bớt một phút lướt, thêm một phút an.","Nghe trong chánh niệm, vị khác hẳn.","Cái lặng ở đây quý hơn vạn lời.","Từng nhịp như từng bước kinh hành.","Nghe xong thấy thương mình hơn một chút.","Đời bận mấy cũng nên dừng lại nghe.","Tiếng nhạc như nước chảy qua tâm.","Ngồi yên nghe hết bài cũng là một phép tu.","Bao nhiêu mệt mỏi theo hơi thở mà ra.","Nghe để nhớ mình đang sống.","Phút giây này là đủ.","Không cầu gì, chỉ nghe thôi cũng đủ an.","Lòng như mặt hồ sau cơn gió.","Một bài nhạc, một nén tâm hương.","Nghe rồi mới hiểu thế nào là tĩnh.","Chỗ ồn nhất trong mình cũng chịu yên."],
'doithuong': ["Chở con đi học về mở nghe chung.","Ca trực đêm nay có bài này bầu bạn.","Ngồi chờ xe khách nghe hết hai lần.","Cuối tháng áp lực, nghe cho nhẹ đầu.","Mở loa nhỏ nhỏ cho cả phòng trọ nghe.","Đi phụ hồ về nghe mà khỏe lại.","Bán hàng online căng quá, nghe xả stress.","Ông xã mình cũng bắt đầu nghe theo.","Cho bé nghe thay nhạc thiếu nhi, bé chịu lắm.","Nghe trong lúc giặt đồ cũng thấy vui.","Đi chùa về mở tiếp cho đỡ nhớ.","Ngồi thêu nghe cả buổi chiều.","Chạy grab nghỉ trưa nghe một bài rồi chạy tiếp.","Nghe lúc dọn hàng sớm, thấy ngày lành.","Cả xóm mình giờ ai cũng biết bài này.","Đi xa nhà, nghe mà đỡ tủi.","Ăn chay ngày rằm, mở nghe cho trọn.","Ngồi canh nồi bánh, nghe hết album luôn.","Mất ngủ cả tuần, nhờ bài này mà chợp mắt được.","Bữa cơm nhà có nhạc này thấy ấm hẳn."],
'nhinho': ["nghe chill hết nút","bài này gây nghiện nha mn","ai chưa nghe là thiệt đó","cứu cánh những đêm mất ngủ","đỉnh nóc kịch trần","vô đây núp mưa mà ở lại luôn","nhạc gì mà êm dữ vậy trời","tai nghe + bài này = thiên đường","nghe mà quên luôn giờ giấc","bị cuốn thiệt chứ đùa đâu","ét ô ét bài này hay quá","đô thị ồn ào cần lắm bài này","giá mà biết bài này sớm hơn","nghe đi các bạn ơi không phí đâu","tự nhiên thấy yêu đời ghê","deadline dí vẫn phải nghe hết bài","một bài chữa lành đúng nghĩa","ngồi học mà cứ tua lại hoài","ai lướt tới đây là có duyên đó","tối nay lại ngủ ngon rồi"],
'quandiem': ["Giữa thời đại vội vã, những bài thế này là cần thiết.","Nhạc đạo mà làm tử tế thì người trẻ vẫn nghe.","Đây là cách gìn giữ văn hoá bằng ngôn ngữ mới.","Không phải cứ tụng mới là tu, nghe cũng là một pháp.","Âm nhạc tốt nâng người nghe lên, bài này làm được.","Chất liệu dân tộc kết hợp hiện đại rất khéo.","Mong dòng nhạc này được đầu tư dài hơi.","Người làm nội dung tâm linh nên học cách làm này.","Tinh thần từ bi thể hiện qua từng giai điệu.","Nghe nhạc cũng là cách gieo hạt lành vào tâm.","Truyền thống không cũ, chỉ cần cách kể mới.","Giá trị thật thì không cần phô trương.","Bài nhạc có thể là một bài pháp ngắn.","Văn hoá Phật giáo Việt cần thêm những sản phẩm thế này.","Làm nghệ thuật có định hướng thế này đáng trân trọng."],
'nhanxet': ["Không gian âm thanh rộng, nghe rất thoáng.","Bass mềm, không lấn giọng, dễ chịu.","Cách ngắt câu để chữ kịp thấm, tinh tế.","Bài để volume nhỏ vẫn nghe rõ từng lớp.","Nhạc cụ mộc xử lý sạch, không bị rối.","Giai điệu tối giản mà không đơn điệu.","Điểm rơi của điệp khúc đặt rất khéo.","Tiếng ambient nền tạo chiều sâu tốt.","Bản này thu giọng gần, nghe ấm.","Cấu trúc bài gọn, không dông dài.","Âm sắc chuông chọn chuẩn, ngân vừa đủ.","Nhịp thả chậm mà vẫn giữ được mạch.","Bài này đeo tai nghe mới thấy hết cái hay.","Cách dùng khoảng lặng đắt giá.","Hòa âm nghe hiện đại mà không mất chất thiền.","Chuyển đoạn mượt, không gãy mạch cảm xúc."],
'hook': ["Ai đang nghe một mình lúc nửa đêm không?","Có ai như mình, nghe xong cứ ngồi im một lúc?","Mọi người thường nghe bài này khi nào?","Ai nghe khi đang chạy xe điểm danh nào?","Có ai nghe mà tự nhiên nhớ quê không?","Nghe cái này lúc mưa có ai giống mình?","Ai đã thuộc lời rồi giơ tay?","Có ai mở cho ba mẹ nghe chưa?","Mình hay nghe lúc thiền, còn mọi người?","Ai phát hiện chỗ hay ở đoạn giữa chưa?","Có ai nghe để dỗ giấc ngủ như mình không?","Người thứ mấy nghìn nghe bài này đây?","Ai vừa nghe vừa đọc bình luận như mình không?","Có ai vòng lại nghe lần ba chưa?","Khung giờ vàng nghe bài này là mấy giờ theo mọi người?"],
'reply': ["Mình đây chứ ai.","Tưởng mỗi mình vậy chứ.","Giơ cả hai tay luôn.","Chuẩn không cần chỉnh.","Mình nghe lúc chạy bộ nè.","Cùng cảnh ngộ nha bạn.","Nhà mình cũng vậy nè.","Mình vòng lại lần năm rồi.","Nghe bạn nói thấy vui ghê.","Đúng rồi đó bạn.","Mình cũng mới phát hiện ra.","Cho mình một vé đồng cảm.","Mưa với bài này là chân ái.","Mình thuộc từ tuần trước rồi nè.","Ba mình nghe xong hỏi bài gì hay vậy.","Thêm mình nữa là đủ hội.","Cũng đang đọc bình luận đây.","Mình nghe từ hồi mới đăng.","Khuya nào cũng gặp nhau ở đây ha.","Bạn nói câu nào trúng câu đó."],
}

PRE=["","","","","Ui ","Chà ","Nói thật là ","Công nhận ","Thiệt tình ","Hmm ","Ôi ","Phải nói là "]
SUF=["","","","","."," ."," ạ."," nha."," á."," ghê."," thiệt luôn."," đó mọi người."," 🙏"," ❤️"," 🪷"," :)"," hihi"," hehe"]

def strip_dia(s):
    s=unicodedata.normalize('NFD',s)
    return ''.join(c for c in s if unicodedata.category(c)!='Mn').replace('đ','d').replace('Đ','D')

def variants(b, tone):
    out={b}
    core=b.rstrip('.!')
    low=core[0].lower()+core[1:]
    casual = tone in ('nhinho','reply','doithuong','tanthan','hook')
    for _ in range(14):
        p=random.choice(PRE); sf=random.choice(SUF)
        if b.endswith('?'):
            v=(p+low+'?') if p else b
            if sf in (' 🙏',' :)',' hihi',' hehe'): v=v[:-1]+'?'+sf
        else:
            v=p+ (low if p else core) + sf
        out.add(v.strip())
    if casual:
        nd=strip_dia(low)
        out.add(nd)
        out.add(strip_dia(core))
    return out

db=sqlite3.connect(DB); c=db.cursor()
ins=0
for tone,arr in MORE.items():
    for b in arr:
        for v in variants(b,tone):
            v=re.sub(r'\s+',' ',v).strip()
            if len(v)<3: continue
            try: c.execute("insert into comment_pool(tone,body) values(?,?)",(tone,v)); ins+=1
            except sqlite3.IntegrityError: pass
# nhân bản biến thể cho base cũ (đợt 1) để tăng kho
olds=c.execute("select tone,body from comment_pool").fetchall()
for tone,b in olds:
    if random.random()<0.5: continue
    core=b.rstrip('.!')
    if b.endswith('?'): continue
    for _ in range(4):
        p=random.choice(PRE); sf=random.choice(SUF)
        v=re.sub(r'\s+',' ',(p+(core[0].lower()+core[1:] if p else core)+sf)).strip()
        if len(v)<3: continue
        try: c.execute("insert into comment_pool(tone,body) values(?,?)",(tone,v)); ins+=1
        except sqlite3.IntegrityError: pass
db.commit()
tot=c.execute("select count(*) from comment_pool where used=0").fetchone()[0]
print(f"added={ins} pool_unused={tot}")
