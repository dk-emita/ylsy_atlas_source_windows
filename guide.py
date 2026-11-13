"""The 60-page MEB 1416 ABD guide, mapped to actual PDF page numbers.
Source pages are 1-indexed *PDF* pages (printed page +5).
Use as workflow guidance, not as a 2025/2026 binding eligibility ruling.
"""

GUIDE = [
# section, title, actual PDF page, level, overview, group
('1','Başlarken',6,0,'Lisansüstü başvuru sürecini ve rehberin kapsamını tanı.','Başlangıç'),
('1.1','Lisansüstü eğitim dereceleri',7,1,'MS, PhD ve profesyonel dereceler arasındaki farkları değerlendir.','Başlangıç'),
('2','Doktora programlarına başvuru',9,0,'Doktora programlarına hazırlık ve araştırma sürecini yönet.','Araştırma'),
('2.1','Planlama',9,1,'Takvim oluştur; uluslararası öğrenci son tarihlerini ve YLSY süresini birlikte izle.','Araştırma'),
('2.2','Üniversite ve program araştırması',11,1,'Sıralama, bölüm, laboratuvar ve danışman uygunluğunu araştır.','Araştırma'),
('2.2.1','Amerikan üniversitelerini tanıyalım',11,2,'Üniversitelerin lisansüstü bölüm ve araştırma sayfalarını incele.','Araştırma'),
('2.2.2','Genel tarama',12,2,'Araştırma alanına uygun alternatif programları geniş bir havuzda topla.','Araştırma'),
('2.2.3','Üniversite bazlı sadeleştirme',12,2,'Coğrafya, yaşam maliyeti ve MEB kısıtlama listesini kontrol et.','Araştırma'),
('2.2.4','Program bazlı sadeleştirme',12,2,'Süre, koşullar, iki uygun tam zamanlı hoca, ders yükü ve politika belgelerini kontrol et.','Araştırma'),
('2.2.5','Önceliklendirme',15,2,'Kritik koşulları karşılamayan seçenekleri ele, güçlü programları grupla.','Araştırma'),
('2.2.6','Nihai liste',15,2,'Danışman görüşmelerine göre başvuru listesini tamamla.','Araştırma'),
('2.3','Bölüm ve profesörlerle iletişim',16,1,'Akademisyen, bölüm ve araştırma öğrencileriyle iletişim planı oluştur.','İletişim'),
('2.3.1','Profesörlerle iletişim',17,2,'Güncel araştırma ve kontenjan bilgilerini öğren; iletişim geçmişini kaydet.','İletişim'),
('2.3.1.1','Profesörlerle iletişimin faydaları',17,3,'Araştırma uyumunu ve danışman kabul durumunu teyit et.','İletişim'),
('2.3.1.2','E-posta oluşturma',18,3,'Üç kısa paragraf, ilgili yayın ve CV ekli kişiselleştirilmiş taslak hazırla.','İletişim'),
('2.3.1.3','E-posta gönderme',19,3,'İlgili hocanın çalışma saatlerini ve akademik takvimini gözet.','İletişim'),
('2.3.1.4','Takip e-postası',19,3,'Yanıt gelmezse rehberde anlatılan uygun takip zamanını değerlendir.','İletişim'),
('2.3.2','Lisansüstü öğrencileriyle iletişim',20,2,'Laboratuvarın çalışma biçimini mevcut öğrencilerden öğren.','İletişim'),
('3','Başvuru sistemi ve gerekli belgeler',21,0,'Programların talep ettiği her belgeyi, tarihini ve durumunu izle.','Başvuru'),
('3.1','Başvuru portalı',21,1,'Programın resmî portalını bul ve başvuru hesabını oluştur.','Başvuru'),
('3.2','Kişisel bilgiler',22,1,'Başvuru bilgilerinin doğruluğunu ve tutarlılığını kontrol et.','Başvuru'),
('3.3','Diploma',23,1,'Diploma/mezuniyet belgesini ve varsa resmî İngilizce çevirisini hazırla.','Belgeler'),
('3.4','Not durum belgesi / transkript',23,1,'Bütün yükseköğretim transkriptlerini ve gerekli İngilizce nüshaları hazırla.','Belgeler'),
('3.4.1','WES ve kredilendirme kurumları',24,2,'Program istenirse WES/denk değerlendirme gereğini kontrol et.','Belgeler'),
('3.5','GRE ve GMAT',24,1,'Güncel sınav politikasını her programa özel doğrula.','Başvuru'),
('3.6','Dil yeterliliği',25,1,'IELTS/TOEFL gereklilikleri ve MEB dil sürecini ayrı ayrı takip et.','Dil'),
('3.7','Tavsiye mektupları',29,1,'Referansları belirle, başvuru portalı taleplerini ve teslimleri izle.','Belgeler'),
('3.8','Niyet mektupları (PS / SoP / Research)',31,1,'Akademik geçmiş, araştırma hedefi ve laboratuvar uyumunu anlatan metinler hazırla.','Belgeler'),
('3.9','Programların özel istekleri',33,1,'Varsa diversity statement, tanıtım videosu veya özel metin taleplerini kaydet.','Belgeler'),
('3.10','Yazı örneği (Writing Sample)',34,1,'Yayın, tez veya istenen yazı örneğini program yönergesine göre hazırla.','Belgeler'),
('3.11','Özgeçmiş (CV / Resume)',34,1,'Araştırma, projeler, teknik beceriler ve yayın odaklı akademik CV düzenle.','Belgeler'),
('3.12','Başvuru ücretleri',36,1,'Ücretleri ve burs kapsamında karşılanma koşullarını teyit et.','Başvuru'),
('4','Mülakat',36,0,'Tanışma görüşmesi ve kabul komitesi mülakatına hazırlan.','Sonuç'),
('4.1','Profesörle ilk mülakat',36,1,'Projelerini, araştırma hedefini ve sorularını prova et.','Sonuç'),
('4.2','Komiteyle son mülakat',37,1,'Motivasyon, teknik yetkinlik, araştırma geçmişi ve kariyer hedeflerini hazırla.','Sonuç'),
('5','Kabul ve ret mektupları',38,0,'Kabul, bekleme listesi ve ret durumunu kayıt altına al.','Sonuç'),
('6','Vize süreci',39,0,'Kabul sonrası ABD vize türünü, DS-2019/DS-160/SEVIS adımlarını güncel kaynaklardan doğrula.','YLSY'),
('7','Sonuç',42,0,'Bütün başvuru aşamalarının nihai kontrolünü tamamla.','Sonuç'),
('EK-1','Profesörlerle iletişim: örnek e-posta',47,0,'Rehberin örnek e-posta şablonunu PDF içinde aç.','Örnekler'),
('EK-2','Tavsiye mektubu taslağı',49,0,'Referans mektubu iskeletini rehberde görüntüle.','Örnekler'),
('EK-3','Akademik özgeçmiş taslağı',50,0,'Akademik CV şablonunu rehberde görüntüle.','Örnekler'),
('EK-4','Zayıf tavsiye mektubu örneği',52,0,'Zayıf referans mektubu örneğini karşılaştırmalı incele.','Örnekler'),
('EK-5','Güçlü tavsiye mektubu örneği',53,0,'Güçlü referans mektubu örneğini karşılaştırmalı incele.','Örnekler'),
('EK-6','Açıklamalı niyet mektubu örneği — 1',54,0,'Açıklamalı örnek niyet mektubunun ilkini incele.','Örnekler'),
('EK-7','Açıklamalı niyet mektubu örneği — 2',56,0,'Açıklamalı örnek niyet mektubunun ikincisini incele.','Örnekler'),
('EK-8','Açıklamalı Statement of Purpose',58,0,'SoP açıklamalı örneğini incele.','Örnekler'),
]

EXTRA_TASKS = [
 ('Dil','TED dil eğitimi boyunca haftalık İngilizce çalışma planını sürdür','2026-12-31','IELTS'),
 ('Dil','IELTS Academic için ilk seviyelendirme denemesini yap','','IELTS'),
 ('Dil','IELTS sınav tarihi için hazır oluş düzeyini değerlendir','','IELTS'),
 ('YLSY','YLSY 2025 resmî yerleştirme kurumunu ve alanını doğrula','','İdari'),
 ('YLSY','MEB’den öğrenime başlama son tarihini yazılı teyit et','','İdari'),
 ('YLSY','REBUS’ta harçsız pasaport belgesi sürecini kontrol et','','Pasaport'),
 ('YLSY','Bordo pasaport için gerekli evrak ve randevuyu hazırla','','Pasaport'),
 ('YLSY','YLSY ülke/alan sıralaması ve kısıtlama listesi uygunluğunu teyit et','','İdari'),
 ('Belgeler','Üç akademik referans adayını belirle','','Başvuru'),
 ('Belgeler','Akademik projelerini yöntem / sonuç / katkı olarak dokümante et','','Başvuru'),
 ('Araştırma','Potansiyel danışmanların 2027 öğrenci kabulünü ayrı ayrı teyit et','','Başvuru'),
]

SCHOOLS = [
 ('Pennsylvania State University','ABD','University Park, PA','https://www.me.psu.edu/students/graduate/admissions.aspx','Penn State',1),
 ('The University of Texas at Austin','ABD','Austin, TX','https://me.utexas.edu/academics/graduate/graduate-admissions','UT Austin',2),
 ('University of Oxford','Birleşik Krallık','Oxford','https://www.ox.ac.uk/admissions/graduate/courses/dphil-engineering-science','Oxford',3),
 ('Purdue University','ABD','West Lafayette, IN','https://engineering.purdue.edu/ME/Graduate/Prospective','Purdue',4),
 ('Massachusetts Institute of Technology','ABD','Cambridge, MA','https://aeroastro.mit.edu/education/graduate-admission/','MIT',5),
]
PROGRAMS = [
 ('Penn State','Mechanical Engineering — PhD','START / ExCCL','Turbine cooling, conjugate heat transfer, aero-thermal tests','2026-12-01'),
 ('UT Austin','Mechanical Engineering — PhD','TTCRL','Film cooling, shaped holes, experimental heat transfer','2026-12-01'),
 ('Oxford','Engineering Science — DPhil','Oxford Thermofluids Institute','Turbine cooling, CFD, CHT, multidisciplinary optimization','2027-03-02'),
 ('Purdue','Mechanical Engineering / AAE — PhD','CFD & Heat Transfer Laboratory','CFD, internal / film cooling, conjugate heat transfer',''),
 ('MIT','Aeronautics and Astronautics — Graduate','Gas Turbine Laboratory','Turbomachinery, propulsion, high-temperature materials','2026-12-01'),
]
ADVISORS = [
 ('Penn State','Stephen Lynch','Convection / experimental heat transfer','https://sites.psu.edu/turbine/',''),
 ('Penn State','Reid Berdanier','Gas turbine performance, experiments','https://sites.psu.edu/turbine/',''),
 ('UT Austin','David G. Bogard','Film cooling and turbine heat transfer','https://sites.utexas.edu/ttcrl/',''),
 ('Oxford','Peter Ireland','Turbine heat transfer and cooling','https://oti.eng.ox.ac.uk/',''),
 ('Oxford','Li He','CFD, CHT, aerothermal and structural interactions','https://oti.eng.ox.ac.uk/',''),
 ('Purdue','Tom Shih','Computational gas turbine aerothermal research','https://engineering.purdue.edu/CFD/',''),
 ('MIT','Zoltán Spakovszky','Turbomachinery and aircraft propulsion','https://www.gas-turbine-lab.mit.edu/',''),
 ('MIT','Zachary Cordero','High-temperature materials and manufacturing','https://www.gas-turbine-lab.mit.edu/',''),
]

TEMPLATES = [
 ('Akademik CV — Taslak','CV','EK-3',50,"""<h1>Akademik Özgeçmiş</h1><p><strong>Ad Soyad</strong> · E-posta · Şehir</p><h2>Araştırma ilgi alanları</h2><p>[İlgilendiğiniz bilimsel alanlar, uzmanlaşmayı hedeflediğiniz konular]</p><h2>Eğitim</h2><p>[Üniversite, bölüm, mezuniyet yılı, GPA]</p><h2>Araştırma ve projeler</h2><p>[Proje, yöntem, kullandığım yazılım, kişisel katkım ve ölçülebilir sonuç]</p><h2>Teknik yetkinlikler</h2><p>[CFD / sonlu elemanlar / CAD / programlama / deneysel yöntemler]</p><h2>Yayınlar ve sunumlar</h2><p>[Yayınlar veya sunumlar; yoksa bu bölümü çıkar]</p><h2>Sertifikalar ve ödüller</h2><p>[İlgili belgeler]</p>"""),
 ('Statement of Purpose — Çalışma Taslağı','SoP','EK-8',58,"""<h1>Statement of Purpose</h1><p><em>Bu metin kişiselleştirilmiş bir çalışma şablonudur; hazır kabul mektubu değildir.</em></p><h2>Research motivation</h2><p>My research interest focuses on [specific research area, motivated problem and intended scientific contribution].</p><h2>Academic preparation</h2><p>[Üniversite eğitimi, önemli projeler ve teknik beceriler]</p><h2>Proposed research direction</h2><p>[Araştırma sorusu + yöntem + doğrulama + beklenen bilimsel katkı]</p><h2>Why this university / advisor</h2><p>[İlgili öğretim üyesinin doğrulanmış çalışmaları ve ortak araştırma sorusu]</p><h2>Future contributions</h2><p>[YLSY sonrasındaki bilimsel hedef]</p>"""),
 ('Potansiyel danışmana ilk e-posta','E-posta','EK-1',47,"""<h1>Prospective PhD Student — [Department / Semester]</h1><p>Dear Professor [Surname],</p><p>I am a prospective doctoral applicant supported by the Turkish Ministry of National Education YLSY scholarship. My academic background is in [discipline] and my research interests include [specific topic and methodology].</p><p>I read your work on [specific, verified paper or project]. I am particularly interested in [research connection and a concise, specific question].</p><p>Would you be accepting new doctoral students for [entry term]? I have attached my academic CV for context. Thank you for your time and consideration.</p><p>Best regards,<br>[Full Name]</p>"""),
 ('Referans mektubu — Yazara bilgi notu','Referans','EK-2',49,"""<h1>Referans Yazarı İçin Bilgi Notu</h1><p><em>Referans mektubunu referans veren kişi kendi görüşüyle yazmalıdır. Bu belge ona iletilecek bilgi özeti olarak kullanılabilir.</em></p><h2>Başvuru</h2><p>[Üniversite, program, son tarih, mektup gönderim sistemi]</p><h2>Birlikte çalışma geçmişi</h2><p>[Ders / proje / laboratuvar, yıl, performans ve katkılar]</p><h2>Somut örnekler</h2><p>[Problemi tanımlama, bağımsız araştırma, takım çalışması, teknik beceriler]</p><h2>Ekler</h2><p>[CV, transkript, araştırma hedefi]</p>"""),
 ('Araştırma önerisi — Temel iskelet','Araştırma','2.2',11,"""<h1>Research Concept Note</h1><h2>Problem definition</h2><p>[Araştırma konunuzdaki açık problem ve gerekçesi]</p><h2>Research question</h2><p>[Kapsamı net, doğrulanabilir araştırma sorusu]</p><h2>Methodology</h2><p>[Yöntem, deney/tasarım/hesaplama adımları, doğrulama ve analiz]</p><h2>Validation plan</h2><p>[Literatür, mesh study, referans deney verileri veya laboratuvar deneyi]</p><h2>Expected scientific contribution</h2><p>[Ölçülebilir yenilik ve sınırlar]</p>"""),
]


# Read-only supplemental drafting templates. They never create personal records until clicked.
# These are original editable instructional samples, not copies of pages in the MEB PDF.
TEMPLATES.extend([
 ('Akademik referans mektubu — Yazara örnek','Referans','EK-2',49,"""<h1>Academic Letter of Recommendation — Sample</h1><p><em>Eğitim amaçlı şablondur. Mektubun gerçek içeriğini yalnızca referans yazarı belirlemelidir.</em></p><p>[Institution letterhead] · [Date]</p><p>Dear Members of the Admissions Committee,</p><p>I am writing to recommend [Applicant] for admission to the [Program] at [University]. I have known the applicant for [duration] as [course instructor / research supervisor] at [Institution].</p><p>In [specific course or project], [Applicant] demonstrated [specific ability]. A concrete example is [the technical problem, applicant's contribution and observed outcome].</p><p>These observations suggest readiness for doctoral research because [evidence of independence, persistence and research judgment]. I recommend [Applicant] for your consideration.</p><p>Sincerely,<br>[Referee name, title, institutional email]</p><p><em>Doğrulanmamış başarı veya deneyim yazmayın; son değerlendirme ve gönderim referans yazarına aittir.</em></p>"""),
 ('Zayıf referans mektubu — Öğretici karşılaştırma','Örnek','EK-4',52,"""<h1>Zayıf Referans Mektubunu Tanıma</h1><p><em>Bu örnek yeni yazılmış bir karşılaştırma metnidir; MEB rehberindeki EK-4'ün birebir metni değildir.</em></p><p>Dear Admissions Committee,</p><p>The applicant attended my class and was a good student. They were polite, punctual, and I believe they will succeed in your program.</p><p>Sincerely, [Referee]</p><h2>Bu neden zayıf?</h2><ul><li>Referans yazarı adayla nasıl çalıştığını açıklamıyor.</li><li>Akademik veya araştırma becerilerini doğrulayacak somut örnek yok.</li><li>Doktora programıyla bağlantı kurulmamış.</li><li>Karşılaştırmalı değerlendirme veya özel katkı görünmüyor.</li></ul><p>Kaynak rehberdeki orijinal örnek: EK-4, PDF s. 52.</p>"""),
 ('Güçlü referans mektubu — Öğretici karşılaştırma','Örnek','EK-5',53,"""<h1>Güçlü Akademik Referans Mektubu — Öğretici Örnek</h1><p><em>Bu örnek gerçek bir aday hakkında yazılmamıştır; MEB PDF metninin kopyası değildir.</em></p><p>Dear Members of the Admissions Committee,</p><p>I supervised [Applicant] during a semester-long numerical heat-transfer project in [Year]. The work required a grid-independence assessment, careful boundary-condition selection and interpretation of uncertainty.</p><p>[Applicant] independently identified an inconsistency between simulation and reference data, designed a controlled sensitivity study, and documented the correction. The resulting analysis was presented clearly to our research group. Compared with other students I have supervised in similar projects, [Applicant] demonstrated particularly strong [specific, documented competency].</p><p>Based on these direct observations, I believe [Applicant] has the technical foundation and research habits to succeed in a demanding graduate environment. I support the application to [Program].</p><p>Sincerely,<br>[Referee name and academic affiliation]</p><h2>Kontrol listesi</h2><ul><li>Yazarın adayla ilişkisi ve gözlem süresi açık mı?</li><li>Ölçülebilir veya doğrulanabilir örnek var mı?</li><li>Bağımsız araştırma yeteneği gerekçelendiriliyor mu?</li><li>Akademisyenin gerçek görüşünü yansıtıyor mu?</li></ul>"""),
 ('Personal Statement — Kişisel motivasyon taslağı','Personal Statement','3.8',31,"""<h1>Personal Statement</h1><p><em>Bu belge adayın kişisel motivasyonunu anlatır; SoP'nin akademik odağından farklıdır.</em></p><h2>Background and motivation</h2><p>[Mühendisliğe / araştırmaya yönelmeni sağlayan somut, gerçek deneyim]</p><h2>Challenge and learning</h2><p>[Karşılaştığın zorluk, kendi kararın, aldığın ders; abartısız ve dürüst örnek]</p><h2>Community and collaboration</h2><p>[Ekip çalışması, öğretme, mentorluk veya akademik ortama katkı]</p><h2>Future direction</h2><p>[Program deneyimini hangi amaç için değerlendireceksin?]</p><p><em>Üniversitenin sayfa ve içerik sınırını esas al.</em></p>"""),
 ('Research Statement — Araştırma planı','Research Statement','3.8',31,"""<h1>Research Statement</h1><h2>Research question</h2><p>[Kısıtlı ve sınanabilir bir bilimsel problem tanımı]</p><h2>Prior preparation</h2><p>[Önceki araştırman, kullanılan yöntemler ve elde edilen doğrulanabilir sonuçlar]</p><h2>Proposed methodology</h2><p>[Deney veya model, veri doğrulama, belirsizlik, sınırlamalar, zamanlama]</p><h2>Expected scholarly contribution</h2><p>[Mevcut bilgiye hangi özgün katkıyı yapabilirsin?]</p><h2>Faculty and laboratory alignment</h2><p>[Güncel ve gerçekten okuduğun bir çalışma ile bağlantı]</p>"""),
 ('Niyet mektubu — Açıklamalı örnek plan 1','Niyet','EK-6',54,"""<h1>Statement of Purpose — Örnek Plan 1</h1><p><em>Özgün çalışma iskeleti. Rehberdeki açıklamalı orijinal mektup: PDF s. 54.</em></p><h2>1. Research motivation</h2><p>[Problemi araştırmaya seni yönelten gerçek bir proje veya gözlemle açıkla.]</p><h2>2. Research preparation</h2><p>[Projede üstlendiğin rolü, doğrulama yöntemini, bulgularını ve sınırlamaları anlat.]</p><h2>3. Current scientific question</h2><p>[Doktorada araştırmak istediğin mekanizmayı ve neden önemli olduğunu anlat.]</p><h2>4. Program fit</h2><p>[Danışmanın doğrulanmış makalesi, laboratuvar imkânı ve senin özgün katkı hedefin.]</p><h2>5. Career contribution</h2><p>[Doktora sonrasındaki araştırma hedefin ve YLSY bağlamındaki dönüş planı.]</p>"""),
 ('Niyet mektubu — Açıklamalı örnek plan 2','Niyet','EK-7',56,"""<h1>Statement of Purpose — Örnek Plan 2</h1><p><em>Özgün ikinci yaklaşım. Rehberdeki açıklamalı örnek: PDF s. 56.</em></p><h2>1. Define the technical challenge</h2><p>[Araştırma alanındaki belirli bir sorunu alan diliyle tanımla.]</p><h2>2. Your strongest evidence</h2><p>[En ilgili tez, staj veya projeden iki somut örnek; kişisel katkı ve ölçülebilir sonuç.]</p><h2>3. Methodological strengths and gaps</h2><p>[Bilinen yöntemler, öğrenmek istediklerin, doktora gerekliliği.]</p><h2>4. Lab and advisor connection</h2><p>[Gerçek yayınlarla belgelenen karşılıklı araştırma uyumu.]</p><h2>5. Future scientific direction</h2><p>[Beklenen araştırma katkısı ve kariyer planı.]</p>"""),
 ('Statement of Purpose — Açıklamalı başvuru kontrolü','SoP','EK-8',58,"""<h1>Statement of Purpose — Final Review</h1><p><em>EK-8 PDF s. 58'deki örneği ayrıca okuyun. Bu metin ayrı bir düzenlenebilir kontrol taslağıdır.</em></p><h2>Opening: research direction</h2><p>[1–2 cümle; ölçülebilir araştırma hedefini tanımlar.]</p><h2>Evidence: prior work</h2><p>[2 güçlü proje, kullandığın yöntem, kişisel katkın ve gerçek bulguların.]</p><h2>Research plan and fit</h2><p>[Hoca/laboratuvar seçimini somut yayınlarla gerekçelendir.]</p><h2>Why doctoral study?</h2><p>[Akademik boşluk ile eğitim gerekliliği bağlantısını kur.]</p><h2>Closing</h2><p>[Gelecekteki araştırma yönün ve katkın.]</p><h2>Final check</h2><ul><li>Üniversiteye özel yazıldı mı?</li><li>Her iddia somut örnekle destekleniyor mu?</li><li>Gereksiz klişe var mı?</li><li>Kelime sınırına uyuldu mu?</li></ul>"""),
 ('Akademik yazı örneği — Kapak notu','Writing Sample','3.10',34,"""<h1>Writing Sample — Submission Note</h1><p>Title of submitted writing sample: [Title]</p><p>Original context: [Course / Thesis / Independent project, year]</p><p>Your contribution: [What you personally wrote or analyzed]</p><p>Research question and method: [Summary]</p><p>Key finding and limitations: [Summary]</p><p><em>Orijinal yazı örneğini ayrıca ekle; bu kapak metni makalenin yerini tutmaz.</em></p>"""),
 ('Diversity Statement — İstenirse','Özel Belge','3.9',33,"""<h1>Diversity Statement — Conditional Template</h1><p><em>Yalnızca başvurulan üniversite resmen istiyorsa hazırlanmalıdır. Güncel ve programa özel yönergeyi kontrol et.</em></p><h2>Relevant experience</h2><p>[Farklı geçmişlerden kişilerle gerçek işbirliği veya eğitim deneyimi]</p><h2>Learning and contribution</h2><p>[Neyi öğrendin ve akademik topluluğa hangi somut katkıyı sunabilirsin?]</p>"""),
 ('Danışmana takip e-postası','E-posta','2.3.1.4',19,"""<h1>Follow-up: Prospective PhD Inquiry — [Program / Term]</h1><p>Dear Professor [Surname],</p><p>I am following up on my email sent on [date] regarding possible doctoral research opportunities in [specific topic]. I remain very interested in your group's work on [verified project or paper] and would appreciate any guidance on whether you expect to consider new students for [term].</p><p>Thank you for your time.</p><p>Best regards,<br>[Full Name]</p><p><em>İlk mesajdan yaklaşık iki hafta sonra, nazikçe ve yalnızca gerektiğinde gönder.</em></p>"""),
])
