##################
# منطق التقارير #
##################
"""
بدل seed
خدمة إدارة قوالب التحاليل
"""
import json
from models.database import getdb


def seed_templates():
    """
    إضافة القوالب الأساسية لقاعدة البيانات
    """
    conn = getdb()
    cur = conn.cursor()

    # قالب CBC
    cbc_fields = [
        {"name": "wbc", "unit": "10^9/l", "normal_range": "4-10"},
        {"name": "rbc", "unit": "10^12/l", "normal_range": "4.5-5.5"},
        {"name": "hgb", "unit": "g/dl", "normal_range": "12-16"},
        {"name": "plt", "unit": "10^9/l", "normal_range": "150-400"},
    ]
    
    cur.execute("""
        INSERT OR IGNORE INTO analysis_templates (analysis_name, fields)   
        VALUES (?, ?)
    """, ("CBC", json.dumps(cbc_fields)))

    # قالب Serology
    serology_fields = [
        {"name": "hiv", "unit": "", "normal_range": "Non-Reactive"},
        {"name": "hep_b", "unit": "", "normal_range": "Non-Reactive"},
    ]
    
    cur.execute("""
        INSERT OR IGNORE INTO analysis_templates (analysis_name, fields)   
        VALUES (?, ?)
    """, ("SEROLOGY", json.dumps(serology_fields)))

    # =======================================
    # قالب RFT (Renal Function Test)
    # =======================================
    rft_fields = [
        {"name": "creatinine", "unit": "mg/dL", "normal_range": "0.7-1.3"},
        {"name": "urea", "unit": "mg/dL", "normal_range": "15-40"},
        {"name": "uric_acid", "unit": "mg/dL", "normal_range": "3.5-7.2"},
    ]
    
    cur.execute("""
        INSERT OR IGNORE INTO analysis_templates (analysis_name, fields)   
        VALUES (?, ?)
    """, ("RFT", json.dumps(rft_fields)))

    # =======================================
    # قالب LFT (Liver Function Test)
    # =======================================
    lft_fields = [
        {"name": "alt", "unit": "U/L", "normal_range": "7-56"},
        {"name": "ast", "unit": "U/L", "normal_range": "10-40"},
        {"name": "alp", "unit": "U/L", "normal_range": "44-147"},
        {"name": "bilirubin_total", "unit": "mg/dL", "normal_range": "0.3-1.2"},
        {"name": "albumin", "unit": "g/dL", "normal_range": "3.5-5.5"},
    ]
    
    cur.execute("""
        INSERT OR IGNORE INTO analysis_templates (analysis_name, fields)   
        VALUES (?, ?)
    """, ("LFT", json.dumps(lft_fields)))

    conn.commit()
    conn.close()
    print("✅ Templates seeded successfully.")


if __name__ == "__main__":
    seed_templates()