from flask import render_template, request, redirect, url_for, session, flash
from functools import wraps
from app import create_app

app = create_app()
app.secret_key = "hotel_booking_secret_key"


# =========================================================
# DECORATOR
# =========================================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("dang_nhap"))
        return f(*args, **kwargs)
    return decorated_function


def owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("dang_nhap"))
        if session.get("vai_tro") != 1:
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function


# =========================================================
# TRANG CHỦ — code partner
# =========================================================
@app.route("/")
def index():
    return render_template("index.html", hotel_cards=[])


# =========================================================
# TÌM KIẾM — code partner
# =========================================================
@app.route("/tim-kiem")
def tim_kiem():
    return render_template("TimKiemKhachSan.html",
        hotel_cards=[], amenities=[],
        keyword="", city="", checkin="", checkout="",
        so_nguoi_lon="2", so_phong="1",
        gia_tu="", gia_den="", so_sao="",
        chinh_sach_huy="", sort_by="goi_y",
        selected_tien_ich=[], total_results=0
    )


# =========================================================
# CHI TIẾT KHÁCH SẠN — code partner
# =========================================================
@app.route("/khach-san/<int:hotel_id>")
def chi_tiet_khach_san(hotel_id):
    return render_template("ChiTietKhachSan.html", data={})


# =========================================================
# ĐĂNG KÝ
# =========================================================
@app.route("/dang-ky", methods=["GET", "POST"])
def dang_ky():
    return render_template("DangKy.html")


# =========================================================
# ĐĂNG KÝ ĐỐI TÁC
# =========================================================
@app.route("/dang-ky-doi-tac", methods=["GET", "POST"])
def dang_ky_doi_tac():
    return render_template("DangKyDoiTac.html")


# =========================================================
# ĐĂNG NHẬP
# =========================================================
@app.route("/dang-nhap", methods=["GET", "POST"])
def dang_nhap():
    return render_template("DangNhap.html")


# =========================================================
# ĐĂNG XUẤT
# =========================================================
@app.route("/dang-xuat")
def dang_xuat():
    session.clear()
    return redirect(url_for("index"))


# =========================================================
# HỒ SƠ
# =========================================================
@app.route("/ho-so")
@login_required
def ho_so():
    return render_template("HoSo.html", user=None, bookings=[])


# =========================================================
# ĐƠN ĐẶT PHÒNG
# =========================================================
@app.route("/dat-phong-cua-toi")
@login_required
def dat_phong_cua_toi():
    return render_template("DatPhongCuaToi.html", bookings=[])


# =========================================================
# DASHBOARD CHỦ KHÁCH SẠN
# =========================================================
@app.route("/quan-ly")
@owner_required
def chu_khach_san_dashboard():
    return render_template("owner/Dashboard.html", hotels=[])


# =========================================================
# TẠO KHÁCH SẠN
# =========================================================
@app.route("/quan-ly/tao-khach-san", methods=["GET", "POST"])
@owner_required
def tao_khach_san():
    return render_template("owner/TaoKhachSan.html", tien_ichs=[])


# =========================================================
# QUẢN LÝ CHI TIẾT KHÁCH SẠN
# =========================================================
@app.route("/quan-ly/khach-san/<int:hotel_id>")
@owner_required
def quan_ly_khach_san(hotel_id):
    return render_template("owner/QuanLyKhachSan.html", hotel=None)


# =========================================================
# INJECT USER
# =========================================================
@app.context_processor
def inject_user():
    return dict(current_user=None)

# =========================================================
# QUẢN LÝ LOẠI PHONGF CỦA KS
# =========================================================
@app.route("/quan-ly/khach-san/<int:hotel_id>/loai-phong")
def quan_ly_loai_phong(hotel_id):


    return render_template("QuanLyLoaiPhong.html")

# =========================================================
# QUẢN LÝ LOẠI PHONGF CỦA KS, CHỉnh SỬA
# =========================================================
@app.route("/quan-ly/khach-san/<int:hotel_id>/loai-phong/<int:room_id>/chinh-sua", methods=["GET", "POST"])
def chinh_sua_loai_phong(hotel_id, room_id):

    return render_template("ChinhSuaLoaiPhong.html")

# =========================================================
# QUẢN LÝ LOẠI PHONGF CỦA KS, CHỉnh SỬA, Xóa ảnh
# =========================================================
@app.route("/quan-ly/khach-san/<int:hotel_id>/loai-phong/<int:room_id>/xoa-anh", methods=["POST"])
def xoa_anh_loai_phong(hotel_id, room_id):
    return redirect(url_for("chinh_sua_loai_phong"))


# =========================================================
# QUẢN LÝ LOẠI PHONGF CỦA KS, CHỉnh SỬA, Xóa ảnh, ĐỔi trạng thái
# =========================================================
@app.route("/quan-ly/loai-phong/<int:room_id>/doi-trang-thai")
def doi_trang_thai_loai_phong(room_id):

    return redirect(url_for("quan_ly_loai_phong"))

# =========================================================
# DẶT PHÒNG KS
# =========================================================
@app.route("/dat_phong/<int:hotel_id>/<int:room_id>")
def dat_phong(hotel_id, room_id):

    return render_template("DatPhong.html")

# =========================================================
# THANH TOÁN
# =========================================================
@app.route("/thanh-toan/momo/<int:hotel_id>/<int:room_id>")
def thanh_toan_momo(hotel_id, room_id):

   return render_template("ThanhToanMoMo.html")


if __name__ == "__main__":
    app.run(debug=True)