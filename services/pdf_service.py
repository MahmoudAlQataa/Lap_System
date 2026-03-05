"""
===============================================
خدمة توليد ملفات PDF
===============================================
يحتوي على:
- دالة توليد PDF للتقرير (generate_pdf)

التغييرات الرئيسية:
--------------------
✅ استقبال analysis_id بدل report_id
✅ جلب البيانات من analysis_instances + patients
✅ حفظ pdf_path في analysis_instances
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from arabic_reshaper import reshape
from bidi.algorithm import get_display

from models.database import getdb
from config import FONT_PATH, HEADER_IMAGE_PATH, PDF_OUTPUT_DIR


def generate_pdf(analysis_id):
    """
    توليد ملف PDF للتحليل
    
    Parameters:
    -----------
    analysis_id: int
        معرف التحليل (من جدول analysis_instances)
    
    Returns:
    --------
    str: مسار ملف PDF المحفوظ
    None: إذا فشل التوليد
    
    الخطوات:
    ---------
    1. جلب بيانات التحليل والمريض
    2. جلب نتائج التحليل
    3. إنشاء المجلدات (سنة/شهر)
    4. إنشاء ملف PDF
    5. رسم Header و Footer
    6. كتابة البيانات والنتائج
    7. حفظ المسار في قاعدة البيانات
    """
    
    # =======================================
    # فتح اتصال بقاعدة البيانات
    # =======================================
    conn = getdb()
    cur = conn.cursor()

    # =======================================
    # جلب بيانات التحليل مع بيانات المريض
    # =======================================
    # ✅ تغيير: JOIN بين analysis_instances و patients
    cur.execute("""
        SELECT 
            p.patient_name,          -- [0] اسم المريض
            p.patient_id_number,     -- [1] رقم الهوية
            p.phone,                 -- [2] الهاتف
            p.age,                   -- [3] العمر
            p.gender,                -- [4] الجنس
            p.doctor_name,           -- [5] الطبيب ✅ جديد
            a.analysis_type,         -- [6] نوع التحليل
            a.created_at             -- [7] التاريخ
        FROM analysis_instances a
        JOIN patients p ON a.patient_id = p.id
        WHERE a.id = ?
    """, (analysis_id,))

    analysis = cur.fetchone()
    
    # =======================================
    # التحقق من وجود البيانات
    # =======================================
    if not analysis:
        conn.close()
        return None

    # =======================================
    # جلب نتائج التحليل
    # =======================================
    # ✅ تغيير: نجيب normal_range كمان
    cur.execute("""
        SELECT field_name, field_value, unit, normal_range
        FROM results
        WHERE analysis_id = ?
    """, (analysis_id,))
    
    results = cur.fetchall()
    conn.close()

    # =======================================
    # إنشاء المجلدات حسب السنة والشهر
    # =======================================
    now = datetime.now()
    year = now.strftime("%Y")   # مثال: 2025
    month = now.strftime("%m")  # مثال: 02
    folder_path = os.path.join(PDF_OUTPUT_DIR, year, month)

    # إنشاء المجلدات إذا لم تكن موجودة
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # =======================================
    # تحديد اسم الملف
    # =======================================
    # نستخدم اسم المريض + معرف التحليل
    patient_name = analysis[0].replace(" ", "_")  # استبدال المسافات بـ _
    pdf_path = os.path.join(folder_path, f"{patient_name}_{analysis_id}.pdf")

    # =======================================
    # إنشاء ملف PDF
    # =======================================
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4  # 595.27 x 841.89 points

    # =======================================
    # تسجيل الخط العربي
    # =======================================
    try:
        pdfmetrics.registerFont(TTFont('Arabic', FONT_PATH))
        arabic_font_available = True
    except:
        arabic_font_available = False

    # =======================================
    # رسم HEADER (صورة الترويسة)
    # =======================================
    header_height = 85  # 3cm تقريباً
    
    if os.path.exists(HEADER_IMAGE_PATH):
        c.drawImage(
            HEADER_IMAGE_PATH, 
            0, 
            height - header_height, 
            width=width, 
            height=header_height, 
            preserveAspectRatio=False
        )
    
    # خط تحت الهيدر
    c.line(0, height - header_height, width, height - header_height)

    # =======================================
    # رسم FOOTER (نص التذييل)
    # =======================================
    footer_height = 57  # 2cm تقريباً
    
    # خط فوق الفوتر
    c.line(0, footer_height, width, footer_height)
    
    # النص في الفوتر (بالعربي إذا متوفر)
    if arabic_font_available:
        c.setFont("Arabic", 10)
        arabic_text1 = get_display(reshape("مرخص من وزارة الصحة الفلسطينية"))
        c.drawCentredString(width/2, footer_height - 15, arabic_text1)
        c.line(50, footer_height - 25, width - 50, footer_height - 25)
        arabic_text2 = get_display(reshape("غزة - شارع الوحدة - مقابل عيادة الدرج (البندر)"))
        c.drawCentredString(width/2, footer_height - 40, arabic_text2)
    else:
        c.setFont("Helvetica", 10)
        c.drawCentredString(width/2, footer_height - 15, "Licensed by Palestinian Ministry of Health")
        c.line(50, footer_height - 25, width - 50, footer_height - 25)
        c.drawCentredString(width/2, footer_height - 40, "Gaza - Al-Wehda Street")

    # =======================================
    # رسم المحتوى الرئيسي
    # =======================================
    y = height - header_height - 30  # البداية تحت الهيدر
    margin_left = 50

    # -----------------------------------------------
    # عنوان Patient Info
    # -----------------------------------------------
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, y, "Patient Info")
    y -= 30

    # -----------------------------------------------
    # بيانات المريض
    # -----------------------------------------------
    # الاسم (بالخط العربي)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin_left, y, "Name:")
    if arabic_font_available:
        c.setFont("Arabic", 11)
        name_arabic = get_display(reshape(analysis[0]))
        c.drawString(margin_left + 60, y, name_arabic)
    else:
        c.setFont("Helvetica", 11)
        c.drawString(margin_left + 60, y, analysis[0])
    y -= 20

    # باقي البيانات
    c.setFont("Helvetica", 11)
    c.drawString(margin_left, y, f"ID: {analysis[1]}")
    y -= 20
    c.drawString(margin_left, y, f"Phone: {analysis[2]}")
    y -= 20
    c.drawString(margin_left, y, f"Age: {analysis[3]}")
    y -= 20
    c.drawString(margin_left, y, f"Gender: {analysis[4]}")
    y -= 20
    
    # ✅ جديد: الطبيب المعالج
    if analysis[5]:  # إذا في طبيب
        c.drawString(margin_left, y, f"Doctor: {analysis[5]}")
        y -= 20
    
    c.drawString(margin_left, y, f"Analysis: {analysis[6]}")
    y -= 40

    # -----------------------------------------------
    # عنوان Results
    # -----------------------------------------------
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, y, "Results")
    y -= 25

    # -----------------------------------------------
    # نتائج التحليل
    # -----------------------------------------------
    c.setFont("Helvetica", 11)
    for r in results:
        # حماية من الكتابة فوق الفوتر
        if y < footer_height + 70:
            break
        
        field_name = r[0] if r[0] else "N/A"
        field_value = r[1] if r[1] else "N/A"
        unit = r[2] if r[2] else ""
        normal_range = r[3] if r[3] else ""  # ✅ جديد
        
        # بناء السطر
        line = f"{field_name} : {field_value} {unit}"
        
        # إضافة normal_range إذا موجود
        if normal_range:
            line += f"  (Normal: {normal_range})"
        
        c.drawString(margin_left, y, line)
        y -= 20

    # =======================================
    # حفظ ملف PDF
    # =======================================
    c.save()

    # =======================================
    # حفظ المسار في قاعدة البيانات
    # =======================================
    # ✅ تغيير: في جدول analysis_instances بدل patients
    conn = getdb()
    cur = conn.cursor()
    cur.execute("""
        UPDATE analysis_instances
        SET pdf_path = ?
        WHERE id = ?
    """, (pdf_path, analysis_id))
    conn.commit()
    conn.close()

    # =======================================
    # إرجاع مسار الملف
    # =======================================
    return pdf_path

def generate_comprehensive_pdf(patient_id):
    """
    توليد PDF شامل لجميع تحاليل المريض
    
    Parameters:
    -----------
    patient_id: int
        معرف المريض
    
    Returns:
    --------
    str: مسار ملف PDF الشامل
    None: إذا فشل التوليد
    
    الوظيفة:
    ---------
    - يجمع كل تحاليل المريض في ملف PDF واحد
    - كل تحليل في قسم منفصل مع عنوان
    """
    
    # =======================================
    # فتح اتصال بقاعدة البيانات
    # =======================================
    conn = getdb()
    cur = conn.cursor()

    # =======================================
    # جلب بيانات المريض
    # =======================================
    cur.execute("""
        SELECT patient_name, patient_id_number, phone, age, gender, doctor_name, created_at
        FROM patients
        WHERE id = ?
    """, (patient_id,))
    
    patient = cur.fetchone()
    
    if not patient:
        conn.close()
        return None

    # =======================================
    # جلب جميع تحاليل المريض
    # =======================================
    cur.execute("""
        SELECT id, analysis_type, created_at
        FROM analysis_instances
        WHERE patient_id = ?
        ORDER BY created_at
    """, (patient_id,))
    
    analyses = cur.fetchall()
    
    if not analyses:
        conn.close()
        return None

    # =======================================
    # إنشاء المجلدات
    # =======================================
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    folder_path = os.path.join(PDF_OUTPUT_DIR, year, month)

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # =======================================
    # تحديد اسم الملف
    # =======================================
    patient_name = patient[0].replace(" ", "_")
    pdf_path = os.path.join(folder_path, f"{patient_name}_comprehensive_{patient_id}.pdf")

    # =======================================
    # إنشاء ملف PDF
    # =======================================
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    # تسجيل الخط العربي
    try:
        pdfmetrics.registerFont(TTFont('Arabic', FONT_PATH))
        arabic_font_available = True
    except:
        arabic_font_available = False

    # =======================================
    # رسم HEADER
    # =======================================
    def draw_header_footer(c, y_start):
        """دالة مساعدة لرسم الهيدر والفوتر"""
        header_height = 85
        footer_height = 57
        
        # Header
        if os.path.exists(HEADER_IMAGE_PATH):
            c.drawImage(HEADER_IMAGE_PATH, 0, height - header_height, 
                        width=width, height=header_height, preserveAspectRatio=False)
        c.line(0, height - header_height, width, height - header_height)
        
        # Footer
        c.line(0, footer_height, width, footer_height)
        
        if arabic_font_available:
            c.setFont("Arabic", 10)
            arabic_text1 = get_display(reshape("مرخص من وزارة الصحة الفلسطينية"))
            c.drawCentredString(width/2, footer_height - 15, arabic_text1)
            c.line(50, footer_height - 25, width - 50, footer_height - 25)
            arabic_text2 = get_display(reshape("غزة - شارع الوحدة - مقابل عيادة الدرج (البندر)"))
            c.drawCentredString(width/2, footer_height - 40, arabic_text2)
        else:
            c.setFont("Helvetica", 10)
            c.drawCentredString(width/2, footer_height - 15, "Licensed by Palestinian Ministry of Health")
            c.line(50, footer_height - 25, width - 50, footer_height - 25)
            c.drawCentredString(width/2, footer_height - 40, "Gaza - Al-Wehda Street")
        
        return header_height, footer_height
    
    # رسم الهيدر والفوتر
    header_height, footer_height = draw_header_footer(c, 0)
    
    # =======================================
    # رسم المحتوى
    # =======================================
    y = height - header_height - 30
    margin_left = 50

    # عنوان Patient Info
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, y, "Comprehensive Report")
    y -= 25
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width/2, y, "Patient Information")
    y -= 30

    # بيانات المريض
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin_left, y, "Name:")
    if arabic_font_available:
        c.setFont("Arabic", 11)
        name_arabic = get_display(reshape(patient[0]))
        c.drawString(margin_left + 60, y, name_arabic)
    else:
        c.setFont("Helvetica", 11)
        c.drawString(margin_left + 60, y, patient[0])
    y -= 20

    c.setFont("Helvetica", 11)
    c.drawString(margin_left, y, f"ID: {patient[1]}")
    y -= 20
    c.drawString(margin_left, y, f"Phone: {patient[2]}")
    y -= 20
    c.drawString(margin_left, y, f"Age: {patient[3]}")
    y -= 20
    c.drawString(margin_left, y, f"Gender: {patient[4]}")
    y -= 20
    
    if patient[5]:
        c.drawString(margin_left, y, f"Doctor: {patient[5]}")
        y -= 20
    
    c.drawString(margin_left, y, f"Date: {patient[6]}")
    y -= 40

    # =======================================
    # رسم كل تحليل
    # =======================================
    for idx, analysis in enumerate(analyses):
        analysis_id = analysis[0]
        analysis_type = analysis[1]
        
        # جلب نتائج هذا التحليل
        cur.execute("""
            SELECT field_name, field_value, unit, normal_range
            FROM results
            WHERE analysis_id = ?
        """, (analysis_id,))
        
        results = cur.fetchall()
        
        # التحقق من المساحة المتبقية
        # إذا ما في مساحة كافية، نبدأ صفحة جديدة
        if y < footer_height + 200:
            c.showPage()
            header_height, footer_height = draw_header_footer(c, 0)
            y = height - header_height - 30
        
        # عنوان التحليل
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(width/2, y, f"Analysis {idx + 1}: {analysis_type}")
        y -= 25
        
        # النتائج
        c.setFont("Helvetica", 11)
        for r in results:
            if y < footer_height + 70:
                c.showPage()
                header_height, footer_height = draw_header_footer(c, 0)
                y = height - header_height - 30
                # إعادة كتابة عنوان التحليل
                c.setFont("Helvetica-Bold", 14)
                c.drawCentredString(width/2, y, f"{analysis_type} (continued)")
                y -= 25
                c.setFont("Helvetica", 11)
            
            field_name = r[0] if r[0] else "N/A"
            field_value = r[1] if r[1] else "N/A"
            unit = r[2] if r[2] else ""
            normal_range = r[3] if r[3] else ""
            
            line = f"{field_name} : {field_value} {unit}"
            if normal_range:
                line += f"  (Normal: {normal_range})"
            
            c.drawString(margin_left, y, line)
            y -= 20
        
        # خط فاصل بين التحاليل
        y -= 10
        c.line(margin_left, y, width - margin_left, y)
        y -= 20

    # =======================================
    # حفظ الملف
    # =======================================
    c.save()
    conn.close()
    
    return pdf_path