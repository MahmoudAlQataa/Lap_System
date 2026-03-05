#########################
# ملف التطبيق الرئيسي #
#########################

from flask import Flask

# استيراد الـ routes
from routes.patients import patients_bp
from routes.reports import reports_bp
from routes.print_routes import print_bp

app = Flask(__name__)

# تسجيل الـ Blueprints
app.register_blueprint(patients_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(print_bp)


@app.route("/")
def home():
    return 'Lab System is Running 🏥'


if __name__ == "__main__":
    # =======================================
    # إنشاء قاعدة البيانات والبيانات الأولية
    # =======================================
    from models.schema import init_database
    from services.template_service import seed_templates
    from services.seed_doctors import seed_doctors  # ✅ جديد
    
    # إنشاء الجداول
    init_database()
    
    # إضافة القوالب
    seed_templates()
    
    # إضافة الأطباء ✅ جديد
    seed_doctors()
    
    # =======================================
    # تشغيل التطبيق
    # =======================================
    app.run(debug=False, use_reloader=False)