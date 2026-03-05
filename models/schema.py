"""
===============================================
ملف إنشاء جداول قاعدة البيانات
===============================================
هذا الملف يحتوي على تعريف جميع الجداول (Tables) في قاعدة البيانات
يُستخدم مرة واحدة عند بداية التطبيق لإنشاء الجداول إذا لم تكن موجودة

الجداول:
---------
1. patients: بيانات المرضى الأساسية
2. doctors: قائمة الأطباء
3. analysis_instances: التحاليل المتعددة لكل مريض
4. results: نتائج التحاليل
5. analysis_templates: القوالب الجاهزة للتحاليل
"""

import sqlite3
from config import DB_NAME


def init_database():
    """
    دالة إنشاء جميع جداول قاعدة البيانات
    
    الوظيفة:
    ---------
    - تفتح اتصال بقاعدة البيانات
    - تنشئ الجداول إذا لم تكن موجودة (CREATE TABLE IF NOT EXISTS)
    - تحفظ التغييرات (commit)
    - تغلق الاتصال
    
    ملاحظة:
    --------
    IF NOT EXISTS تعني: أنشئ الجدول فقط إذا لم يكن موجوداً
    فائدة: نقدر نشغل هذه الدالة أكثر من مرة بدون مشاكل
    """
    
    # =======================================
    # فتح اتصال بقاعدة البيانات
    # =======================================
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # =======================================
    # جدول المرضى (patients)
    # =======================================
    # يخزن: بيانات المريض الأساسية فقط
    # ملاحظة: analysis_type تم نقله لجدول analysis_instances
    cur.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            -- المعرف الفريد للمريض (يزيد تلقائياً)
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- اسم المريض الكامل
            patient_name TEXT NOT NULL,
            
            -- رقم الهوية
            patient_id_number TEXT,
            
            -- رقم الهاتف
            phone TEXT,
            
            -- الجنس (Male/Female)
            gender TEXT,
            
            -- العمر (رقم صحيح)
            age INTEGER,
            
            -- اسم الطبيب المعالج
            -- سيتم ربطه بجدول doctors لاحقاً
            doctor_name TEXT,
            
            -- تاريخ ووقت إنشاء السجل (أول زيارة)
            created_at TEXT NOT NULL
        )
    """)

    # =======================================
    # جدول الأطباء (doctors)
    # =======================================
    # يخزن: قائمة الأطباء المتاحين في القائمة المنسدلة
    # فائدة: سهولة الإضافة والتعديل بدون تعديل الكود
    cur.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            -- المعرف الفريد للطبيب
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- اسم الطبيب الكامل
            -- UNIQUE: لا يمكن تكرار نفس الاسم
            doctor_name TEXT UNIQUE NOT NULL,
            
            -- التخصص (اختياري)
            specialization TEXT,
            
            -- نشط أو غير نشط
            -- 1 = نشط (يظهر في القائمة)
            -- 0 = غير نشط (مخفي)
            is_active INTEGER DEFAULT 1
        )
    """)

    # =======================================
    # جدول التحاليل (analysis_instances)
    # =======================================
    # يخزن: كل تحليل كصف مستقل
    # مثال: مريض عمل CBC + RFT = صفين هنا
    cur.execute("""
        CREATE TABLE IF NOT EXISTS analysis_instances (
            -- المعرف الفريد للتحليل
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- معرف المريض (مرتبط بجدول patients)
            -- كل التحاليل لنفس المريض لها نفس patient_id
            patient_id INTEGER NOT NULL,
            
            -- نوع التحليل (CBC, RFT, LFT, etc.)
            analysis_type TEXT NOT NULL,
            
            -- تاريخ ووقت إجراء التحليل
            created_at TEXT NOT NULL,
            
            -- مسار ملف PDF الخاص بهذا التحليل
            -- ملاحظة: كل تحليل له PDF منفصل
            pdf_path TEXT,
            
            -- تعريف المفتاح الخارجي
            -- يربط التحليل بالمريض
            -- ON DELETE CASCADE: إذا حذفنا المريض، كل تحاليله تنحذف
            FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
        )
    """)

    # =======================================
    # جدول النتائج (results)
    # =======================================
    # يخزن: نتائج التحاليل - كل صف = نتيجة واحدة
    # ملاحظة مهمة: تم تغيير patient_id إلى analysis_id
    cur.execute("""
        CREATE TABLE IF NOT EXISTS results (
            -- المعرف الفريد للنتيجة
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- معرف التحليل (مرتبط بجدول analysis_instances)
            -- هذا هو التغيير الأساسي!
            -- بدل patient_id، صار analysis_id
            analysis_id INTEGER NOT NULL,
            
            -- اسم الحقل (مثلاً: WBC, HGB)
            field_name TEXT NOT NULL,
            
            -- قيمة الحقل (مثلاً: 7.5)
            field_value TEXT,
            
            -- وحدة القياس (مثلاً: g/dL)
            unit TEXT,
            
            -- المدى الطبيعي (مثلاً: 4-10)
            -- قابل للتعديل من الواجهة
            normal_range TEXT,
            
            -- تعريف المفتاح الخارجي
            -- يربط النتيجة بالتحليل
            -- ON DELETE CASCADE: إذا حذفنا التحليل، نتائجه تنحذف
            FOREIGN KEY (analysis_id) REFERENCES analysis_instances(id) ON DELETE CASCADE
        )
    """)

    # =======================================
    # جدول القوالب (analysis_templates)
    # =======================================
    # يخزن: القوالب الجاهزة للتحاليل (CBC, RFT, etc.)
    # كل صف = قالب واحد مع حقوله
    cur.execute("""
        CREATE TABLE IF NOT EXISTS analysis_templates (
            -- المعرف الفريد للقالب
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- اسم التحليل (CBC, SEROLOGY, etc.)
            -- UNIQUE يمنع تكرار نفس الاسم
            analysis_name TEXT UNIQUE NOT NULL,
            
            -- الحقول بصيغة JSON
            -- مثال: [{"name": "wbc", "unit": "10^9/l"}, ...]
            fields TEXT NOT NULL
        )
    """)

    # =======================================
    # حفظ التغييرات
    # =======================================
    # commit() يحفظ كل التغييرات في قاعدة البيانات
    # بدون commit()، التغييرات ما تنحفظ!
    conn.commit()
    
    # =======================================
    # إغلاق الاتصال
    # =======================================
    # مهم: دائماً نغلق الاتصال بعد الانتهاء
    conn.close()
    
    # طباعة رسالة نجاح
    print("✅ Database initialized successfully.")


# =======================================
# تشغيل الكود إذا تم تنفيذ الملف مباشرة
# =======================================
# معناه: إذا شغلت python schema.py
# راح ينفذ الكود التالي
if __name__ == "__main__":
    init_database()