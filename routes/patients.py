"""
===============================================
Routes الخاصة بإدارة المرضى
===============================================
يحتوي على:
- إضافة تقرير جديد (new_report)
- عرض تقرير محدد (view_report)
"""

import json
from datetime import datetime
from flask import Blueprint, render_template, request
from models.database import getdb
from services.pdf_service import generate_pdf

# =======================================
# إنشاء Blueprint للمرضى
# =======================================
# Blueprint يسمح لنا بتنظيم الـ routes في ملفات منفصلة
patients_bp = Blueprint('patients', __name__)


@patients_bp.route("/new-report", methods=["GET", "POST"])
def new_report():
    """
    صفحة إضافة تقرير جديد
    
    التحديثات:
    -----------
    ✅ دعم التحاليل المتعددة
    ✅ معالجة كل تحليل بشكل منفصل
    ✅ توليد PDF لكل تحليل
    """
    
    # =======================================
    # معالجة POST (عند إرسال الفورم)
    # =======================================
    if request.method == "POST":
        
        # =======================================
        # الخطوة 1: جمع بيانات المريض
        # =======================================
        patient_data = {
            "name": request.form.get("name"),
            "patient_id_number": request.form.get("patient_id_number"),
            "phone": request.form.get("phone"),
            "age": request.form.get("age"),
            "gender": request.form.get("gender"),
            "doctor_name": request.form.get("doctor_name"),
        }

        # =======================================
        # الخطوة 2: جمع التحاليل المحددة
        # =======================================
        # ✅ جديد: selected_analyses هي قائمة بأسماء التحاليل
        selected_analyses = request.form.getlist("selected_analyses")
        
        # التحقق من وجود تحاليل محددة
        if not selected_analyses:
            return "Please select at least one analysis type", 400

        # =======================================
        # فتح اتصال بقاعدة البيانات
        # =======================================
        conn = getdb()
        cur = conn.cursor()

        # =======================================
        # الخطوة 3: إضافة المريض
        # =======================================
        created_at = datetime.now().strftime("%Y-%m-%d %I:%M %p")

        cur.execute("""
            INSERT INTO patients
            (patient_name, patient_id_number, phone, gender, age, doctor_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            patient_data["name"],
            patient_data["patient_id_number"],
            patient_data["phone"],
            patient_data["gender"],
            patient_data["age"],
            patient_data["doctor_name"],
            created_at
        ))

        # الحصول على ID المريض
        patient_id = cur.lastrowid
        
        print(f"✅ Patient created with ID: {patient_id}")
        print(f"📋 Selected analyses: {selected_analyses}")

        # =======================================
        # الخطوة 4: معالجة كل تحليل
        # =======================================
        analysis_ids = []  # لحفظ IDs التحاليل
        
        for analysis_type in selected_analyses:
            print(f"\n🔬 Processing {analysis_type}...")
            
            # --------------------------------------
            # 4.1: جلب قالب التحليل
            # --------------------------------------
            cur.execute("""
                SELECT fields
                FROM analysis_templates
                WHERE analysis_name = ?
            """, (analysis_type.upper(),))
            
            template_row = cur.fetchone()
            
            if not template_row:
                print(f"⚠️ Template not found for {analysis_type}")
                continue
            
            template_fields = json.loads(template_row[0])

            # --------------------------------------
            # 4.2: جمع نتائج هذا التحليل
            # --------------------------------------
            # ملاحظة: الحقول بصيغة: CBC_wbc, CBC_wbc_range
            results_data = []
            
            for field in template_fields:
                field_name = field["name"]
                unit = field.get("unit", "")
                
                # ✅ جديد: نجيب القيمة باستخدام اسم التحليل كبريفكس
                value_key = f"{analysis_type}_{field_name}"
                range_key = f"{analysis_type}_{field_name}_range"
                
                value = request.form.get(value_key, "").strip()
                normal_range = request.form.get(range_key, "").strip()
                
                # إذا ما في قيمة من الفورم، استخدم القيمة الافتراضية
                if not normal_range:
                    normal_range = field.get("normal_range", "")
                
                # حفظ فقط إذا في قيمة
                if value:
                    results_data.append({
                        "field_name": field_name,
                        "field_value": value,
                        "unit": unit,
                        "normal_range": normal_range
                    })
            
            print(f"   📊 Found {len(results_data)} results")

            # --------------------------------------
            # 4.3: إضافة التحليل
            # --------------------------------------
            cur.execute("""
                INSERT INTO analysis_instances
                (patient_id, analysis_type, created_at)
                VALUES (?, ?, ?)
            """, (patient_id, analysis_type, created_at))

            analysis_id = cur.lastrowid
            analysis_ids.append(analysis_id)
            print(f"   ✅ Analysis created with ID: {analysis_id}")

            # --------------------------------------
            # 4.4: إضافة النتائج
            # --------------------------------------
            for result in results_data:
                cur.execute("""
                    INSERT INTO results
                    (analysis_id, field_name, field_value, unit, normal_range)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    analysis_id,
                    result["field_name"],
                    result["field_value"],
                    result["unit"],
                    result["normal_range"]
                ))
            
            print(f"   ✅ {len(results_data)} results saved")

        # =======================================
        # حفظ التغييرات
        # =======================================
        conn.commit()
        conn.close()

        # =======================================
        # الخطوة 5: توليد PDF لكل تحليل
        # =======================================
        print(f"\n📄 Generating PDFs...")
        for analysis_id in analysis_ids:
            pdf_path = generate_pdf(analysis_id)
            if pdf_path:
                print(f"   ✅ PDF created: {pdf_path}")

        # =======================================
        # عرض صفحة النجاح
        # =======================================
        
        # ✅ جديد: جلب التحليل النشط من الفورم
        active_analysis_name = request.form.get("active_analysis", "")
        
        # =======================================
        # تجهيز البيانات لصفحة النجاح
        # =======================================
        
        # ✅ إنشاء قائمة بكل التحاليل مع IDs
        analyses_list = []
        for idx, analysis_type in enumerate(selected_analyses):
            analyses_list.append({
                "id": analysis_ids[idx],
                "name": analysis_type,
                "is_active": analysis_type == active_analysis_name
            })
        
        return render_template(
            "success.html", 
            patient_id=patient_id,
            patient=patient_data,
            analyses_list=analyses_list,  # ✅ القائمة الكاملة
            analyses_count=len(analysis_ids)
        )

    # =======================================
    # معالجة GET (عرض الفورم)
    # =======================================
    
    # جلب البيانات للواجهة
    conn = getdb()
    cur = conn.cursor()
    
    # جلب قائمة الأطباء
    cur.execute("""
        SELECT doctor_name 
        FROM doctors 
        WHERE is_active = 1
        ORDER BY doctor_name
    """)
    doctors = [row[0] for row in cur.fetchall()]
    
    # جلب جميع القوالب
    cur.execute("""
        SELECT analysis_name, fields
        FROM analysis_templates
        ORDER BY analysis_name
    """)
    
    templates_data = {}
    for row in cur.fetchall():
        analysis_name = row[0]
        fields = json.loads(row[1])
        templates_data[analysis_name] = fields
    
    conn.close()
    
    # إرسال البيانات للواجهة
    return render_template(
        "patient_form.html", 
        doctors=doctors,
        templates=templates_data
    )
    
    
@patients_bp.route("/reports/<int:report_id>")
def view_report(report_id):
    """
    عرض تقرير محدد
    
    ملاحظة:
    --------
    ✅ نمرر patient_id للواجهة لاستخدامه في الطباعة الشاملة
    ✅ نجيب كل تحاليل المريض لعرض أزرار الطباعة الفردية
    """
    conn = getdb()
    cur = conn.cursor()

    # جلب بيانات التحليل مع بيانات المريض
    cur.execute("""
        SELECT 
            a.id,
            p.patient_name,
            p.patient_id_number,
            p.phone,
            p.age,
            p.gender,
            p.doctor_name,
            a.analysis_type,
            a.created_at,
            a.patient_id
        FROM analysis_instances a
        JOIN patients p ON a.patient_id = p.id
        WHERE a.id = ?
    """, (report_id,))
    
    analysis = cur.fetchone()
    
    if not analysis:
        return "Report not found", 404
    
    patient_id = analysis[9]  # patient_id من الاستعلام

    # ✅ جديد: جلب كل تحاليل المريض
    cur.execute("""
        SELECT id, analysis_type
        FROM analysis_instances
        WHERE patient_id = ?
        ORDER BY created_at
    """, (patient_id,))
    
    all_analyses = cur.fetchall()

    # جلب نتائج التحليل الحالي
    cur.execute("""
        SELECT field_name, field_value, unit, normal_range
        FROM results
        WHERE analysis_id = ?
    """, (report_id,))
    
    results = cur.fetchall()

    conn.close()

    return render_template(
        "report_view.html", 
        patient=analysis, 
        results=results,
        patient_id=patient_id,  # ✅ جديد
        all_analyses=all_analyses  # ✅ جديد
    )