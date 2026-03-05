"""
===============================================
Routes الخاصة بالطباعة والـ PDF
===============================================
يحتوي على:
- فتح ملف PDF المحفوظ (open_pdf)
- صفحة الطباعة (print_report)
"""

from flask import Blueprint, render_template, send_file
from models.database import getdb

# =======================================
# إنشاء Blueprint للطباعة
# =======================================
print_bp = Blueprint('print', __name__)


@print_bp.route("/pdf_reports/<int:report_id>")
def open_pdf(report_id):
    """
    فتح ملف PDF المحفوظ
    
    Parameters:
    -----------
    report_id: int
        معرف التحليل (analysis_id)
    
    Returns:
    --------
    ملف PDF للعرض في المتصفح
    
    ملاحظة:
    --------
    ✅ تغيير: نجيب pdf_path من جدول analysis_instances
    """
    
    # =======================================
    # فتح اتصال بقاعدة البيانات
    # =======================================
    conn = getdb()
    cur = conn.cursor()
    
    # =======================================
    # جلب مسار ملف PDF
    # =======================================
    # ✅ تغيير: من جدول analysis_instances بدل patients
    cur.execute("""
        SELECT pdf_path 
        FROM analysis_instances 
        WHERE id = ?
    """, (report_id,))
    
    result = cur.fetchone()
    
    # =======================================
    # إغلاق الاتصال
    # =======================================
    conn.close()
    
    # =======================================
    # إرسال ملف PDF
    # =======================================
    if result and result[0]:
        return send_file(
            result[0],
            mimetype='application/pdf',
            as_attachment=False,  # عرض في المتصفح (مش تحميل)
            download_name=f'report_{report_id}.pdf'
        )

    # =======================================
    # إذا الملف غير موجود
    # =======================================
    return "PDF not found", 404


@print_bp.route("/print/<int:report_id>")
def print_report(report_id):
    """
    صفحة الطباعة
    
    Parameters:
    -----------
    report_id: int
        معرف التحليل (analysis_id)
    
    Returns:
    --------
    صفحة HTML للطباعة
    
    الوظيفة:
    ---------
    - جلب بيانات التحليل
    - جلب النتائج
    - عرضها في صفحة مهيأة للطباعة
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
            p.patient_name,          -- اسم المريض
            p.patient_id_number,     -- رقم الهوية
            p.phone,                 -- الهاتف
            p.age,                   -- العمر
            p.gender,                -- الجنس
            p.doctor_name,           -- الطبيب ✅ جديد
            a.analysis_type,         -- نوع التحليل
            a.created_at             -- التاريخ
        FROM analysis_instances a
        JOIN patients p ON a.patient_id = p.id
        WHERE a.id = ?
    """, (report_id,))
    
    analysis = cur.fetchone()

    # =======================================
    # جلب نتائج التحليل
    # =======================================
    # ✅ تغيير: نستخدم analysis_id
    cur.execute("""
        SELECT 
            field_name,      -- اسم الحقل
            field_value,     -- القيمة
            unit,            -- الوحدة
            normal_range     -- المدى الطبيعي
        FROM results
        WHERE analysis_id = ?
    """, (report_id,))
    
    results = cur.fetchall()

    # =======================================
    # إغلاق الاتصال
    # =======================================
    conn.close()

    # =======================================
    # عرض صفحة الطباعة
    # =======================================
    return render_template("print.html", patient=analysis, results=results)

@print_bp.route("/print-single/<int:analysis_id>")
def print_single_report(analysis_id):
    """
    طباعة تقرير لتحليل واحد فقط
    
    Parameters:
    -----------
    analysis_id: int
        معرف التحليل
    """
    # نفس الكود الموجود في print_report
    # لكن لتحليل واحد فقط
    return print_report(analysis_id)


@print_bp.route("/print-comprehensive/<int:patient_id>")
def print_comprehensive_report(patient_id):
    """
    طباعة تقرير شامل لجميع تحاليل المريض
    
    Parameters:
    -----------
    patient_id: int
        معرف المريض
    """
    conn = getdb()
    cur = conn.cursor()

    # جلب بيانات المريض
    cur.execute("""
        SELECT patient_name, patient_id_number, phone, age, gender, doctor_name, created_at
        FROM patients
        WHERE id = ?
    """, (patient_id,))
    
    patient = cur.fetchone()

    # جلب جميع التحاليل
    cur.execute("""
        SELECT id, analysis_type
        FROM analysis_instances
        WHERE patient_id = ?
        ORDER BY created_at
    """, (patient_id,))
    
    analyses_list = cur.fetchall()
    
    # جلب نتائج كل تحليل
    all_results = []
    for analysis in analyses_list:
        analysis_id = analysis[0]
        analysis_type = analysis[1]
        
        cur.execute("""
            SELECT field_name, field_value, unit, normal_range
            FROM results
            WHERE analysis_id = ?
        """, (analysis_id,))
        
        results = cur.fetchall()
        
        all_results.append({
            "analysis_type": analysis_type,
            "results": results
        })

    conn.close()

    return render_template("print_comprehensive.html", patient=patient, all_results=all_results)