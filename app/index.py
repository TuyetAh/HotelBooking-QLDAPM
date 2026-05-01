from flask import render_template, request, redirect, url_for, session, flash
from functools import wraps
from app import create_app
import math
from datetime import date, timedelta
from app.dao import (
    build_hotel_card_data,
    get_featured_hotels,
    get_all_amenities,
    search_hotels_advanced,
    get_hotel_detail_data,
    check_login,
    register_user,
    get_user_by_id,
    create_hotel_owner_account, get_bookings_by_user, doi_mat_khau, update_user, create_hotel_full,
    get_all_tien_ich_khach_san, get_hotel_by_id,
)
app = create_app()
app.secret_key = "hotel_booking_secret_key"


# =========================================================
# DECORATOR
# =========================================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Bạn cần đăng nhập để tiếp tục.", "error")
            return redirect(url_for("dang_nhap"))
        return f(*args, **kwargs)
    return decorated_function
def owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Bạn cần đăng nhập.", "error")
            return redirect(url_for("dang_nhap"))
        if session.get("vai_tro") != 1:
            flash("Bạn không có quyền truy cập.", "error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function


# =========================================================
# TRANG CHỦ
# =========================================================
@app.route("/")
def index():
    today = date.today()
    tomorrow = today + timedelta(days=1)
    featured_hotels = get_featured_hotels()
    hotel_cards = [build_hotel_card_data(hotel) for hotel in featured_hotels]
    return render_template("index.html",
                           hotel_cards=hotel_cards,
                           today=today.strftime("%Y-%m-%d"),
                           tomorrow=tomorrow.strftime("%Y-%m-%d")
                           )



# =========================================================
# TÌM KIẾM KHÁCH SẠN
# =========================================================
@app.route("/tim-kiem")
def tim_kiem():
    keyword = request.args.get("keyword", "").strip()
    city = request.args.get("city", "").strip()
    checkin = request.args.get("checkin", "").strip()
    checkout = request.args.get("checkout", "").strip()
    so_nguoi_lon = request.args.get("so_nguoi_lon", "").strip()
    so_phong = request.args.get("so_phong", "").strip()
    gia_tu = request.args.get("gia_tu", "").strip()
    gia_den = request.args.get("gia_den", "").strip()
    so_sao = request.args.get("so_sao", "").strip()
    chinh_sach_huy = request.args.get("chinh_sach_huy", "").strip()
    sort_by = request.args.get("sort_by", "goi_y").strip()

    tien_ich_ids = request.args.getlist("tien_ich")

    hotels = search_hotels_advanced(
        keyword=keyword,
        city=city,
        checkin=checkin,
        checkout=checkout,
        so_nguoi_lon=so_nguoi_lon if so_nguoi_lon else None,
        so_phong=so_phong if so_phong else None,
        gia_tu=gia_tu if gia_tu else None,
        gia_den=gia_den if gia_den else None,
        so_sao=so_sao if so_sao else None,
        tien_ich_ids=tien_ich_ids,
        chinh_sach_huy=chinh_sach_huy if chinh_sach_huy else None,
        sort_by=sort_by
    )

    hotel_cards = [
        build_hotel_card_data(
            hotel,
            checkin=checkin,
            checkout=checkout,
            so_nguoi_lon=so_nguoi_lon,
            so_phong=so_phong
        )
        for hotel in hotels
    ]
    amenities = get_all_amenities()
    page = request.args.get("page", 1, type=int)
    per_page = 5

    total_results = len(hotel_cards)
    total_pages = math.ceil(total_results / per_page)

    start = (page - 1) * per_page
    end = start + per_page

    hotel_cards_page = hotel_cards[start:end]

    if not keyword or not checkin or not checkout:
        flash("Vui lòng nhập địa điểm, ngày nhận phòng và ngày trả phòng.", "error")
        return redirect(url_for("index"))

    return render_template(
        "TimKiemKhachSan.html",
        hotel_cards=hotel_cards_page,
        total_results=total_results,
        page=page,
        total_pages=total_pages,
        amenities=amenities,
        keyword=keyword,
        city=city,
        checkin=checkin,
        checkout=checkout,
        so_nguoi_lon=so_nguoi_lon or "2",
        so_phong=so_phong or "1",
        gia_tu=gia_tu,
        gia_den=gia_den,
        so_sao=so_sao,
        chinh_sach_huy=chinh_sach_huy,
        sort_by=sort_by,
        selected_tien_ich=tien_ich_ids
    )

# =========================================================
# CHI TIẾT KHÁCH SẠN
# =========================================================
@app.route("/khach-san/<int:hotel_id>")
def chi_tiet_khach_san(hotel_id):
    checkin = request.args.get("checkin", "").strip()
    checkout = request.args.get("checkout", "").strip()
    so_nguoi_lon = request.args.get("so_nguoi_lon", "2").strip()
    so_phong = request.args.get("so_phong", "1").strip()

    data = get_hotel_detail_data(
        hotel_id=hotel_id,
        checkin=checkin,
        checkout=checkout,
        so_nguoi_lon=so_nguoi_lon,
        so_phong=so_phong
    )
    if request.args and (not checkin or not checkout or not so_nguoi_lon or not so_phong):
        flash("Vui lòng nhập đầy đủ ngày nhận phòng, ngày trả phòng, số người lớn và số phòng.", "error")
        return redirect(url_for("chi_tiet_khach_san", hotel_id=hotel_id))
    if not data:
        flash("Không tìm thấy khách sạn.", "error")
        return redirect(url_for("index"))

    return render_template("ChiTietKhachSan.html", data=data)


# =========================================================
# ĐĂNG KÝ
# =========================================================
@app.route("/dang-ky", methods=["GET", "POST"])
def dang_ky():
    if request.method == "POST":
        ho_ten = request.form.get("fullname")
        ten_dang_nhap = request.form.get("username")
        mat_khau = request.form.get("password")
        so_dien_thoai = request.form.get("phone")
        email = request.form.get("email")
        so_tai_khoan_ngan_hang = request.form.get("bank_account")

        if not ho_ten or not ten_dang_nhap or not mat_khau or not so_dien_thoai or not email:
            return render_template("DangKy.html",
                                   err_msg="Vui lòng nhập đầy đủ các trường bắt buộc.")

        success, result = register_user(
            ten_dang_nhap=ten_dang_nhap,
            mat_khau=mat_khau,
            ho_ten=ho_ten,
            so_dien_thoai=so_dien_thoai,
            email=email,
            so_tai_khoan_ngan_hang=so_tai_khoan_ngan_hang,
            vai_tro=2
        )

        if success:
            flash("Đăng ký tài khoản thành công. Bạn hãy đăng nhập nhé.", "success")
            return redirect(url_for("dang_nhap"))
        else:
            return render_template("DangKy.html", err_msg=result)

    return render_template("DangKy.html")

# =========================================================
# ĐĂNG NHẬP
# =========================================================
@app.route("/dang-nhap", methods=["GET", "POST"])
def dang_nhap():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return render_template("DangNhap.html",
                                   err_msg="Vui lòng nhập tên đăng nhập và mật khẩu.")

        user = check_login(username, password)

        if user:
            session["user_id"] = user.MaNguoiDung
            session["username"] = user.TenDangNhap
            session["ho_ten"] = user.HoTen
            session["vai_tro"] = user.VaiTro
            flash("Đăng nhập thành công.", "success")
            if user.VaiTro == 1:
                return redirect(url_for("chu_khach_san_dashboard"))
            else:
                return redirect(url_for("index"))
        else:
            return render_template("DangNhap.html",
                                   err_msg="Sai tên đăng nhập hoặc mật khẩu.")

    return render_template("DangNhap.html")

# =========================================================
# ĐĂNG XUẤT
# =========================================================
@app.route("/dang-xuat")
def dang_xuat():
    session.clear()
    flash("Bạn đã đăng xuất.", "success")
    return redirect(url_for("index"))


# =========================================================
# HỒ SƠ
# =========================================================
@app.route("/ho-so")
@login_required
def ho_so():
    return render_template("HoSo.html", user=None, bookings=[])


# =========================================================
# INJECT USER CHO MỌI TEMPLATE
# =========================================================
@app.context_processor
def inject_user():
    user_id = session.get("user_id")
    current_user = get_user_by_id(user_id) if user_id else None
    return dict(current_user=current_user)

# =========================================================
# DASHBOARD CHỦ KHÁCH SẠN
# =========================================================
@app.route("/quan-ly")
@owner_required
def chu_khach_san_dashboard():
    from app.dao import get_hotels_by_owner
    user_id = session.get("user_id")
    hotels = get_hotels_by_owner(user_id)
    return render_template("owner/Dashboard.html", hotels=hotels)
# =========================================================
# HỒ SƠ CÁ NHÂN
# =========================================================
@app.route("/ho-so")
@login_required
def ho_so():
    user = get_user_by_id(session.get("user_id"))
    bookings = get_bookings_by_user(session.get("user_id"))
    return render_template("HoSo.html", user=user, bookings=bookings)

# =========================================================
# CHỈNH SỬA THÔNG TIN
# =========================================================
@app.route("/chinh-sua-thong-tin", methods=["POST"])
@login_required
def chinh_sua_thong_tin():
    user_id = session.get("user_id")
    ho_ten = request.form.get("ho_ten")
    so_dien_thoai = request.form.get("so_dien_thoai")
    email = request.form.get("email")
    so_tai_khoan_ngan_hang = request.form.get("so_tai_khoan_ngan_hang")

    success, result = update_user(
        user_id=user_id,
        ho_ten=ho_ten,
        so_dien_thoai=so_dien_thoai,
        email=email,
        so_tai_khoan_ngan_hang=so_tai_khoan_ngan_hang
    )

    if success:
        session["ho_ten"] = result.HoTen
        flash("Cập nhật thông tin thành công.", "success")
    else:
        flash(result, "error")

    return redirect(url_for("ho_so"))


# =========================================================
# ĐỔI MẬT KHẨU
# =========================================================
@app.route("/doi-mat-khau", methods=["POST"])
@login_required
def doi_mat_khau_route():
    user_id = session.get("user_id")
    mat_khau_cu = request.form.get("mat_khau_cu")
    mat_khau_moi = request.form.get("mat_khau_moi")
    xac_nhan_mat_khau = request.form.get("xac_nhan_mat_khau")

    if mat_khau_moi != xac_nhan_mat_khau:
        flash("Mật khẩu mới không khớp.", "error")
        return redirect(url_for("ho_so"))

    if len(mat_khau_moi) < 6:
        flash("Mật khẩu mới phải có ít nhất 6 ký tự.", "error")
        return redirect(url_for("ho_so"))

    success, msg = doi_mat_khau(user_id, mat_khau_cu, mat_khau_moi)

    if success:
        flash("Đổi mật khẩu thành công.", "success")
    else:
        flash(msg, "error")

    return redirect(url_for("ho_so"))

# =========================================================
# ĐĂNG KÝ ĐỐI TÁC / CHỦ KHÁCH SẠN
# =========================================================
@app.route("/dang-ky-doi-tac", methods=["GET", "POST"])
def dang_ky_doi_tac():
    if request.method == "POST":
        ho_ten = request.form.get("fullname")
        ten_dang_nhap = request.form.get("username")
        mat_khau = request.form.get("password")
        so_dien_thoai = request.form.get("phone")
        email = request.form.get("email")
        so_tai_khoan_ngan_hang = request.form.get("bank_account")
        ten_doanh_nghiep = request.form.get("ten_doanh_nghiep")
        dia_chi_doanh_nghiep = request.form.get("dia_chi_doanh_nghiep")

        if not ho_ten or not ten_dang_nhap or not mat_khau or not so_dien_thoai or not email:
            return render_template("DangKyDoiTac.html",
                                   err_msg="Vui lòng nhập đầy đủ các trường bắt buộc.")

        success, result = create_hotel_owner_account(
            ten_dang_nhap=ten_dang_nhap,
            mat_khau=mat_khau,
            ho_ten=ho_ten,
            so_dien_thoai=so_dien_thoai,
            email=email,
            so_tai_khoan_ngan_hang=so_tai_khoan_ngan_hang,
            ten_doanh_nghiep=ten_doanh_nghiep,
            dia_chi_doanh_nghiep=dia_chi_doanh_nghiep
        )

        if success:
            flash("Đăng ký thành công! Vui lòng đăng nhập.", "success")
            return redirect(url_for("dang_nhap"))
        else:
            return render_template("DangKyDoiTac.html", err_msg=result)

    return render_template("DangKyDoiTac.html")

# =========================================================
# TẠO KHÁCH SẠN MỚI
# =========================================================
@app.route("/quan-ly/tao-khach-san", methods=["GET", "POST"])
@owner_required
def tao_khach_san():
    tien_ichs = get_all_tien_ich_khach_san()

    if request.method == "POST":
        ten_khach_san = request.form.get("ten_khach_san")
        thanh_pho = request.form.get("thanh_pho")
        dia_chi = request.form.get("dia_chi")
        vi_tri_noi_bat = request.form.get("vi_tri_noi_bat")
        so_dien_thoai_lien_he = request.form.get("so_dien_thoai_lien_he")
        mo_ta = request.form.get("mo_ta")
        quy_dinh_khach_san = request.form.get("quy_dinh_khach_san")
        chinh_sach_huy = request.form.get("chinh_sach_huy", 0)
        ds_tien_ich = request.form.getlist("tien_ich")

        if not ten_khach_san or not thanh_pho or not dia_chi or not so_dien_thoai_lien_he:
            return render_template("owner/TaoKhachSan.html",
                                   tien_ichs=tien_ichs,
                                   err_msg="Vui lòng nhập đầy đủ các trường bắt buộc.")

        success, result = create_hotel_full(
            user_id=session.get("user_id"),
            ten_khach_san=ten_khach_san,
            thanh_pho=thanh_pho,
            dia_chi=dia_chi,
            vi_tri_noi_bat=vi_tri_noi_bat,
            so_dien_thoai_lien_he=so_dien_thoai_lien_he,
            mo_ta=mo_ta,
            quy_dinh_khach_san=quy_dinh_khach_san,
            chinh_sach_huy=chinh_sach_huy,
            ds_tien_ich=ds_tien_ich
        )

        if success:
            flash("Tạo khách sạn thành công! Vui lòng chờ admin duyệt.", "success")
            return redirect(url_for("chu_khach_san_dashboard"))
        else:
            return render_template("owner/TaoKhachSan.html",
                                   tien_ichs=tien_ichs,
                                   err_msg=result)

    return render_template("owner/TaoKhachSan.html", tien_ichs=tien_ichs)
# QUẢN LÝ CHI TIẾT 1 KHÁCH SẠN
# =========================================================
@app.route("/quan-ly/khach-san/<int:hotel_id>")
@owner_required
def quan_ly_khach_san(hotel_id):
    hotel = get_hotel_by_id(hotel_id)
    if not hotel:
        flash("Không tìm thấy khách sạn.", "error")
        return redirect(url_for("chu_khach_san_dashboard"))
    return render_template("owner/QuanLyKhachSan.html", hotel=hotel)

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