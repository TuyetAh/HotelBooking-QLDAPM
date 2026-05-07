from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

db = SQLAlchemy()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config[
        "SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:Tranhoangkiet%40123@localhost/datphongkhachsan?charset=utf8mb4"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Cấu hình Gmail SMTP
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = "caohuuky5@gmail.com"   # Mail server dùng để gửi mail
    app.config["MAIL_PASSWORD"] = "tvgtiorldrgnjdky"       # ← App Password Gmail tạo từ mail
    app.config["MAIL_DEFAULT_SENDER"] = "caohuuky5@gmail.com"

    # =========================================================
    # MoMo Sandbox Config
    # Thay BASE_URL bằng URL ngrok của bạn khi chạy local
    # =========================================================
    app.config["MOMO_PARTNER_CODE"] = "MOMO"
    app.config["MOMO_ACCESS_KEY"] = "F8BBA842ECF85"
    app.config["MOMO_SECRET_KEY"] = "K951B6PE1waDMi640xX08PD3vg6EkVlz"
    app.config["MOMO_ENDPOINT"] = "https://test-payment.momo.vn/v2/gateway/api/create"
    app.config["BASE_URL"] = "https://impure-suitcase-founder.ngrok-free.dev"

    db.init_app(app)
    mail.init_app(app)

    with app.app_context():
        from app import models
        from app.admin import init_admin
        init_admin(app)

    return app

