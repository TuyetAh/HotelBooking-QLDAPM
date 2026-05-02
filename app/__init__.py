from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote
# Tạo đối tượng SQLAlchemy dùng chung cho toàn bộ project
db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    # Cấu hình chuỗi kết nối database SQL Server
    # sửa lại username, password, server cho đúng máy
    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:140522@localhost/datphongkhachsan?charset=utf8mb4"
    # Tắt cảnh báo không cần thiết
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Gắn db vào app
    db.init_app(app)


    with app.app_context():
        # Import models để SQLAlchemy nhận diện các bảng
        from app import models

    return app






