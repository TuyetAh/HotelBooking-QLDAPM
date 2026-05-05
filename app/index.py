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
    auto_complete_expired_bookings,
    get_hotel_by_id,
    get_room_edit_data,
    update_room_basic_info,
    update_room_amenities,
    save_room_images,
    delete_room_image,
    get_room_types_management_by_hotel,
    get_room_type_by_id,
    update_room_basic_info,
    update_room_status,
    get_booking_detail_for_owner,
    is_room_type_currently_occupied,
    room_type_has_active_or_future_booking,
    room_type_has_any_booking,
    delete_room_type,
    cancel_booking_by_owner,
    create_room_type,
    get_room_amenities_without_db_change,
    ensure_payouts_for_completed_bookings,
    check_login,
    register_user,
    get_user_by_id,
    create_hotel_owner_account, get_bookings_by_user, doi_mat_khau, update_user, create_hotel_full,
    is_hotel_belong_to_owner,
    get_all_tien_ich_khach_san, get_hotel_by_id,
    get_reviews_by_hotel,
    get_completed_bookings_can_review,
    update_hotel_basic_info,
    create_review,
    kiem_tra_co_the_huy_don,
    huy_don_boi_khach_hang,
    get_booking_detail_for_customer,
    create_review,
    get_room_booking_data,
    cleanup_expired_pending_bookings,
    get_pending_booking_page_data,
    delete_expired_pending_booking,
    create_pending_booking,
    create_booking,
    get_booking_by_code,
    create_payment
)
from app.momo import create_momo_payment, verify_ipn_signature
from flask import current_app
from app.models import DatPhong


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
    can_review_bookings = []

    user_id = session.get("user_id")

    if user_id:
        can_review_bookings = get_completed_bookings_can_review(hotel_id, user_id)

    data["can_review_bookings"] = can_review_bookings
    data["reviews"] = get_reviews_by_hotel(hotel_id)

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
            session["user_id"] = int(user.MaNguoiDung)
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
# ĐƠN ĐẶT PHÒNG CỦA TÔI
# =========================================================
@app.route("/dat-phong-cua-toi")
@login_required
def dat_phong_cua_toi():
    bookings = get_bookings_by_user(session.get("user_id"))
    return render_template("DatPhongCuaToi.html", bookings=bookings)

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


# =========================================================
# QUẢN LÝ LOẠI PHONGF CỦA KS
# =========================================================
@app.route("/quan-ly/khach-san/<int:hotel_id>/loai-phong")
@owner_required
def quan_ly_loai_phong(hotel_id):
    user_id = session.get("user_id")

    if not is_hotel_belong_to_owner(hotel_id, user_id):
        flash("Bạn không có quyền quản lý khách sạn này.", "error")
        return redirect(url_for("chu_khach_san_dashboard"))

    tab = request.args.get("tab", "loai-phong")

    data = get_room_types_management_by_hotel(hotel_id, tab=tab)

    if not data:
        flash("Không tìm thấy khách sạn.", "error")
        return redirect(url_for("chu_khach_san_dashboard"))

    return render_template("owner/QuanLyLoaiPhong.html", data=data, tab=tab)

# =========================================================
# QUẢN LÝ LOẠI PHONGF CỦA KS, CHỉnh SỬA
# =========================================================
@app.route("/quan-ly/khach-san/<int:hotel_id>/loai-phong/<int:room_id>/chinh-sua", methods=["GET", "POST"])
def chinh_sua_loai_phong(hotel_id, room_id):
    user_id = session.get("user_id")

    if not is_hotel_belong_to_owner(hotel_id, user_id):
        flash("Bạn không có quyền chỉnh sửa loại phòng của khách sạn này.", "error")
        return redirect(url_for("chu_khach_san_dashboard"))

    data = get_room_edit_data(hotel_id, room_id)

    if not data:
        flash("Không tìm thấy loại phòng.", "error")
        return redirect(url_for("quan_ly_loai_phong", hotel_id=hotel_id))

    if request.method == "POST":
        ten_loai_phong = request.form.get("ten_loai_phong", "").strip()
        mo_ta = request.form.get("mo_ta", "").strip()
        gia_moi_dem = request.form.get("gia_moi_dem", "0").strip()
        so_nguoi_toi_da = request.form.get("so_nguoi_toi_da", "1").strip()
        so_luong_phong = request.form.get("so_luong_phong", "0").strip()
        trang_thai_hoat_dong = request.form.get("trang_thai_hoat_dong", "1").strip()
        amenity_ids = request.form.getlist("tien_ich")

        success, result = update_room_basic_info(
            room_id=room_id,
            ten_loai_phong=ten_loai_phong,
            mo_ta=mo_ta,
            gia_moi_dem=gia_moi_dem,
            so_nguoi_toi_da=so_nguoi_toi_da,
            so_luong_phong=so_luong_phong,
            trang_thai_hoat_dong=int(trang_thai_hoat_dong)
        )

        if not success:
            flash(result, "error")
            return redirect(url_for("chinh_sua_loai_phong", hotel_id=hotel_id, room_id=room_id))

        update_room_amenities(room_id, amenity_ids)

        files = request.files.getlist("room_images")

        if files and files[0].filename != "":
            success_img, message_img = save_room_images(data["room"].ThuMucAnh, files)
            flash(message_img, "success" if success_img else "error")

        flash("Cập nhật loại phòng thành công.", "success")
        return redirect(url_for("chinh_sua_loai_phong", hotel_id=hotel_id, room_id=room_id))

    return render_template("owner/ChinhSuaLoaiPhong.html", data=data)

# =========================================================
# QUẢN LÝ LOẠI PHONGF CỦA KS, CHỉnh SỬA, Xóa ảnh
# =========================================================
@app.route("/quan-ly/khach-san/<int:hotel_id>/loai-phong/<int:room_id>/xoa-anh", methods=["POST"])
def xoa_anh_loai_phong(hotel_id, room_id):
    user_id = session.get("user_id")

    if not is_hotel_belong_to_owner(hotel_id, user_id):
        flash("Bạn không có quyền xóa ảnh của khách sạn này.", "error")
        return redirect(url_for("chu_khach_san_dashboard"))

    filename = request.form.get("filename")
    data = get_room_edit_data(hotel_id, room_id)

    if not data:
        flash("Không tìm thấy loại phòng.", "error")
        return redirect(url_for("quan_ly_loai_phong", hotel_id=hotel_id))

    success, message = delete_room_image(data["room"].ThuMucAnh, filename)

    flash(message, "success" if success else "error")
    return redirect(url_for("chinh_sua_loai_phong", hotel_id=hotel_id, room_id=room_id))


# =========================================================
# QUẢN LÝ LOẠI PHONGF CỦA KS ĐỔi trạng thái
# =========================================================
@app.route("/quan-ly/loai-phong/<int:room_id>/doi-trang-thai")
@owner_required
def doi_trang_thai_loai_phong(room_id):
    room = get_room_type_by_id(room_id)

    if not room:
        flash("Không tìm thấy loại phòng.", "error")
        return redirect(url_for("chu_khach_san_dashboard"))

    user_id = session.get("user_id")

    if not is_hotel_belong_to_owner(room.MaKhachSan, user_id):
        flash("Bạn không có quyền thao tác với loại phòng này.", "error")
        return redirect(url_for("chu_khach_san_dashboard"))


    hotel_id = room.MaKhachSan

    # Nếu đang hoạt động và muốn dừng
    if room.TrangThaiHoatDong == 1:
        if room_type_has_active_or_future_booking(room_id):
            flash("Không thể dừng hoạt động loại phòng này vì đang có đơn đặt phòng hiện tại hoặc sắp tới. Vui lòng hủy các đơn đặt trước rồi thử lại.", "error")
            return redirect(url_for("quan_ly_loai_phong", hotel_id=hotel_id))

        new_status = 0

    # Nếu đang dừng thì cho mở lại bình thường
    else:
        new_status = 1

    success, result = update_room_status(room_id, new_status)

    if success:
        flash("Cập nhật trạng thái loại phòng thành công.", "success")
    else:
        flash(result, "error")

    return redirect(url_for("quan_ly_loai_phong", hotel_id=hotel_id))


# =========================================================
# QUẢN LÝ LOẠI PHONGF CỦA KS, Xem đơn
# =========================================================
@app.route("/quan-ly/dat-phong/<int:booking_id>")
def chi_tiet_don_dat_phong_chu_ks(booking_id):
    data = get_booking_detail_for_owner(booking_id)

    if not data:
        flash("Không tìm thấy đơn đặt phòng.", "error")
        return redirect(url_for("index"))
    user_id = session.get("user_id")
    hotel_id = data["booking"].MaKhachSan

    if not is_hotel_belong_to_owner(hotel_id, user_id):
        flash("Bạn không có quyền xem đơn đặt phòng này.", "error")
        return redirect(url_for("chu_khach_san_dashboard"))

    return render_template(
        "owner/ChiTietDonDatPhongChuKS.html",
        data=data,
        today=date.today()
    )
# =========================================================
# QUẢN LÝ LOẠI PHONGF CỦA KS, Xóa LP
# =========================================================
@app.route("/quan-ly/loai-phong/<int:room_id>/xoa")
def xoa_loai_phong(room_id):
    room = get_room_type_by_id(room_id)

    if not room:
        flash("Không tìm thấy loại phòng.", "error")
        return redirect(url_for("chu_khach_san_dashboard"))

    user_id = session.get("user_id")

    if not is_hotel_belong_to_owner(room.MaKhachSan, user_id):
        flash("Bạn không có quyền xóa loại phòng này.", "error")
        return redirect(url_for("chu_khach_san_dashboard"))

    hotel_id = room.MaKhachSan

    if room_type_has_any_booking(room_id):
        flash("Không thể xóa loại phòng vì loại phòng này đã có đơn đặt phòng. Bạn chỉ có thể dừng hoạt động.", "error")
        return redirect(url_for("quan_ly_loai_phong", hotel_id=hotel_id))

    success, message = delete_room_type(room_id)

    flash(message, "success" if success else "error")
    return redirect(url_for("quan_ly_loai_phong", hotel_id=hotel_id))

# =========================================================
# QUẢN LÝ LOẠI PHONGF CỦA KS, HỦY ĐƠN
# =========================================================
@app.route("/quan-ly/dat-phong/<int:booking_id>/huy", methods=["POST"])
def huy_don_dat_phong_chu_ks(booking_id):
    data = get_booking_detail_for_owner(booking_id)

    if not data:
        flash("Không tìm thấy đơn đặt phòng.", "error")
        return redirect(url_for("chu_khach_san_dashboard"))

    user_id = session.get("user_id")
    hotel_id = data["booking"].MaKhachSan

    if not is_hotel_belong_to_owner(hotel_id, user_id):
        flash("Bạn không có quyền hủy đơn đặt phòng này.", "error")
        return redirect(url_for("chu_khach_san_dashboard"))

    success, message, hotel_id = cancel_booking_by_owner(booking_id)

    flash(message, "success" if success else "error")
    return redirect(url_for("quan_ly_loai_phong", hotel_id=hotel_id, tab="don-dat"))

# =========================================================
# QUẢN LÝ LOẠI PHÒNG CỦA KS, THÊM LP
# =========================================================
@app.route("/quan-ly/khach-san/<int:hotel_id>/loai-phong/them", methods=["GET", "POST"])
@owner_required
def them_loai_phong(hotel_id):
    user_id = session.get("user_id")

    if not is_hotel_belong_to_owner(hotel_id, user_id):
        flash("Bạn không có quyền thao tác với khách sạn này.", "error")
        return redirect(url_for("chu_khach_san_dashboard"))

    hotel = get_hotel_by_id(hotel_id)

    if not hotel:
        flash("Không tìm thấy khách sạn.", "error")
        return redirect(url_for("index"))

    amenities = get_room_amenities_without_db_change()

    if request.method == "POST":
        ten_loai_phong = request.form.get("ten_loai_phong", "").strip()
        mo_ta = request.form.get("mo_ta", "").strip()
        gia_moi_dem = request.form.get("gia_moi_dem", "").strip()
        so_nguoi_toi_da = request.form.get("so_nguoi_toi_da", "").strip()
        so_luong_phong = request.form.get("so_luong_phong", "").strip()
        trang_thai_hoat_dong = request.form.get("trang_thai_hoat_dong", "1")
        amenity_ids = request.form.getlist("tien_ich")

        if not ten_loai_phong or not gia_moi_dem or not so_nguoi_toi_da or not so_luong_phong:
            flash("Vui lòng nhập đầy đủ các trường bắt buộc.", "error")
            return redirect(url_for("them_loai_phong", hotel_id=hotel_id))

        if float(gia_moi_dem) < 1 or int(so_nguoi_toi_da) < 1 or int(so_luong_phong) < 1:
            flash("Giá, sức chứa và số lượng phòng phải lớn hơn hoặc bằng 1.", "error")
            return redirect(url_for("them_loai_phong", hotel_id=hotel_id))

        success, result = create_room_type(
            ma_khach_san=hotel_id,
            ten_loai_phong=ten_loai_phong,
            mo_ta=mo_ta,
            gia_moi_dem=gia_moi_dem,
            so_nguoi_toi_da=int(so_nguoi_toi_da),
            so_luong_phong=int(so_luong_phong),
            trang_thai_hoat_dong=int(trang_thai_hoat_dong),
            amenity_ids=amenity_ids
        )

        if not success:
            flash(result, "error")
            return redirect(url_for("them_loai_phong", hotel_id=hotel_id))

        files = request.files.getlist("room_images")
        if files and files[0].filename != "":
            save_room_images(result.ThuMucAnh, files)

        flash("Thêm loại phòng thành công.", "success")
        return redirect(url_for("quan_ly_loai_phong", hotel_id=hotel_id))

    return render_template(
        "owner/ThemLoaiPhong.html",
        hotel=hotel,
        amenities=amenities
    )
# =========================================================
# Tự dộng ktra và cập nhập mỗi lần web có request
# =========================================================
@app.before_request
def before_request():
    auto_complete_expired_bookings()
    ensure_payouts_for_completed_bookings()
    cleanup_expired_pending_bookings()

# =========================================================
#  ĐÁNH GIÁ VÀ NHẬN XÉT KS
# =========================================================
@app.route("/khach-san/<int:hotel_id>/danh-gia", methods=["POST"])
def them_danh_gia_khach_san(hotel_id):
    user_id = session.get("user_id")

    if not user_id:
        flash("Vui lòng đăng nhập để đánh giá.", "error")
        return redirect(url_for("dang_nhap"))

    ma_dat_phong = request.form.get("ma_dat_phong")
    so_sao = request.form.get("so_sao")
    binh_luan = request.form.get("binh_luan", "").strip()

    if not ma_dat_phong or not so_sao:
        flash("Vui lòng chọn đơn và số sao đánh giá.", "error")
        return redirect(url_for("chi_tiet_khach_san", hotel_id=hotel_id))

    success, message = create_review(
        ma_dat_phong=int(ma_dat_phong),
        ma_nguoi_dung=user_id,
        ma_khach_san=hotel_id,
        so_sao=int(so_sao),
        binh_luan=binh_luan
    )

    flash(message, "success" if success else "error")
    return redirect(url_for("chi_tiet_khach_san", hotel_id=hotel_id))

# =========================================================
# DẶT PHÒNG KS
# =========================================================

@app.route("/dat_phong/<int:hotel_id>/<int:room_id>", methods=["GET", "POST"])
@login_required
def dat_phong(hotel_id, room_id):
   checkin      = request.args.get("checkin", "").strip()
   checkout     = request.args.get("checkout", "").strip()
   so_nguoi_lon = request.args.get("so_nguoi_lon", "2").strip()
   so_phong     = request.args.get("so_phong", "1").strip()

   if not checkin or not checkout:
       flash("Vui lòng chọn ngày nhận phòng và ngày trả phòng.", "error")
       return redirect(url_for("chi_tiet_khach_san", hotel_id=hotel_id))


   data = get_room_booking_data(hotel_id, room_id, checkin, checkout, so_nguoi_lon, so_phong)

   if not data:
       flash("Không tìm thấy thông tin đặt phòng.", "error")
       return redirect(url_for("index"))
   if data["so_phong_con_trong"] < int(so_phong):
       flash("Loại phòng này không còn đủ số lượng phòng trống.", "error")
       return redirect(url_for("chi_tiet_khach_san", hotel_id=hotel_id))

   if request.method == "POST":
       success, result = create_booking(
           user_id=session.get("user_id"),
           hotel_id=hotel_id,
           room_id=room_id,
           checkin=checkin,
           checkout=checkout,
           so_nguoi_lon=so_nguoi_lon,
           so_phong=so_phong,
           tong_tien=data["tong_tien"]
       )
       if not success:
           flash(result, "error")
           return redirect(request.url)


       booking = result
       base_url = current_app.config["BASE_URL"]
       redirect_url = f"{base_url}/momo/return"
       ipn_url      = f"{base_url}/momo/ipn"
       order_info   = f"Dat phong {booking.MaDatPhongCode}"


       momo_resp = create_momo_payment(
           booking_code=booking.MaDatPhongCode,
           amount=int(data["tong_tien"]),
           order_info=order_info,
           redirect_url=redirect_url,
           ipn_url=ipn_url
       )


       if momo_resp.get("resultCode") == 0:
           return redirect(momo_resp["payUrl"])


       flash(f"Lỗi MoMo: {momo_resp.get('message', 'Không xác định')}", "error")
       return redirect(request.url)


   return render_template("DatPhong.html", data=data)

# =========================================================
# TẠO ĐƠN TẠM
# =========================================================
@app.route("/dat-phong/khoi-tao/<int:hotel_id>/<int:room_id>")
@login_required
def khoi_tao_dat_phong(hotel_id, room_id):
   checkin = request.args.get("checkin", "").strip()
   checkout = request.args.get("checkout", "").strip()
   so_nguoi_lon = request.args.get("so_nguoi_lon", "1")
   so_phong = request.args.get("so_phong", "1")

   if not checkin or not checkout:
       flash("Vui lòng chọn ngày nhận phòng và ngày trả phòng trước khi chọn phòng.", "error")
       return redirect(url_for("chi_tiet_khach_san", hotel_id=hotel_id))

   user_id = session.get("user_id")


   success, result = create_pending_booking(
       user_id=user_id,
       hotel_id=hotel_id,
       room_id=room_id,
       checkin=checkin,
       checkout=checkout,
       so_nguoi_luu_tru=int(so_nguoi_lon),
       so_phong=int(so_phong)
   )


   if not success:
       flash(result, "error")
       return redirect(url_for("chi_tiet_khach_san", hotel_id=hotel_id))


   booking_id = result


   print("REDIRECT SANG BOOKING ID:", booking_id)


   return redirect(url_for("dat_phong_theo_don", booking_id=booking_id))


@app.route("/dat-phong/<int:booking_id>")
@login_required
def dat_phong_theo_don(booking_id):
   print("ĐANG MỞ TRANG ĐẶT PHÒNG ID:", booking_id)


   data = get_pending_booking_page_data(
       booking_id=booking_id,
       user_id=session.get("user_id")
   )


   if not data:
       flash("Không tìm thấy đơn đặt phòng.", "error")
       return redirect(url_for("index"))


   return render_template("DatPhong.html", data=data)
# Xóa đơn khi hết 3p
@app.route("/dat-phong/<int:booking_id>/het-han")
@login_required
def het_han_giu_phong(booking_id):
   booking = DatPhong.query.get(booking_id)
   hotel_id = booking.MaKhachSan if booking else None


   success, message = delete_expired_pending_booking(
       booking_id,
       session.get("user_id")
   )


   flash("Đơn giữ phòng đã hết hạn. Vui lòng đặt lại.", "error")


   if hotel_id:
       return redirect(url_for("chi_tiet_khach_san", hotel_id=hotel_id))


   return redirect(url_for("index"))


# =========================================================
# THANH TOÁN
# =========================================================
@app.route("/thanh-toan/momo/<int:booking_id>")
@login_required
def thanh_toan_momo_theo_don(booking_id):
    data = get_pending_booking_page_data(booking_id, session.get("user_id"))

    if not data:
        flash("Không tìm thấy đơn thanh toán.", "error")
        return redirect(url_for("index"))

    booking = data["booking"]

    if booking.TrangThaiDatPhong != 0:
        flash("Đơn này không còn chờ thanh toán.", "error")
        return redirect(url_for("index"))

    amount = int(booking.TongTien)
    order_id = booking.MaDatPhongCode
    request_id = f"{order_id}_{int(datetime.now().timestamp())}"
    order_info = f"Thanh toán đặt phòng {order_id}"

    redirect_url = url_for("momo_return", _external=True)
    ipn_url = url_for("momo_ipn", _external=True)

    request_type = "captureWallet"
    extra_data = ""

    raw_signature = (
        f"accessKey={MOMO_ACCESS_KEY}"
        f"&amount={amount}"
        f"&extraData={extra_data}"
        f"&ipnUrl={ipn_url}"
        f"&orderId={order_id}"
        f"&orderInfo={order_info}"
        f"&partnerCode={MOMO_PARTNER_CODE}"
        f"&redirectUrl={redirect_url}"
        f"&requestId={request_id}"
        f"&requestType={request_type}"
    )

    signature = hmac.new(
        MOMO_SECRET_KEY.encode("utf-8"),
        raw_signature.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    payload = {
        "partnerCode": MOMO_PARTNER_CODE,
        "partnerName": "Hotel Booking",
        "storeId": "HotelBookingStore",
        "requestId": request_id,
        "amount": amount,
        "orderId": order_id,
        "orderInfo": order_info,
        "redirectUrl": redirect_url,
        "ipnUrl": ipn_url,
        "lang": "vi",
        "extraData": extra_data,
        "requestType": request_type,
        "signature": signature
    }

    res = requests.post(MOMO_ENDPOINT, json=payload, timeout=30)
    momo_data = res.json()

    if momo_data.get("resultCode") != 0:
        flash("Không tạo được thanh toán MoMo: " + momo_data.get("message", ""), "error")
        return redirect(url_for("dat_phong_theo_don", booking_id=booking_id))

    return redirect(momo_data["payUrl"])

# =========================================================
# MOMO RETURN — Redirect người dùng về sau khi thanh toán
# =========================================================
@app.route("/momo/return")
def momo_return():
   result_code = request.args.get("resultCode", "-1")
   order_id    = request.args.get("orderId", "")
   amount      = request.args.get("amount", "0")
   message     = request.args.get("message", "")


   booking = get_booking_by_code(order_id)
   success = result_code == "0"


   return render_template("MomoReturn.html",
                          success=success,
                          booking=booking,
                          amount=int(amount),
                          message=message)

# =========================================================
# MOMO IPN — MoMo gọi về đây sau khi thanh toán
# =========================================================
@app.route("/momo/ipn", methods=["POST"])
def momo_ipn():
   data = request.get_json(force=True) or {}


   if not verify_ipn_signature(data):
       return {"resultCode": 1, "message": "Invalid signature"}, 400


   order_id    = data.get("orderId", "")
   result_code = int(data.get("resultCode", -1))
   trans_id    = str(data.get("transId", ""))
   amount      = data.get("amount", 0)


   booking = get_booking_by_code(order_id)
   if not booking:
       return {"resultCode": 1, "message": "Booking not found"}, 404


   if result_code == 0:
       create_payment(
           ma_dat_phong=booking.MaDatPhong,
           phuong_thuc_thanh_toan="MoMo",
           trang_thai_thanh_toan=1,
           so_tien_thanh_toan=amount,
           ma_giao_dich=trans_id,
           thoi_gian_thanh_toan=date.today()
       )
   else:
       create_payment(
           ma_dat_phong=booking.MaDatPhong,
           phuong_thuc_thanh_toan="MoMo",
           trang_thai_thanh_toan=2,
           so_tien_thanh_toan=amount,
           ma_giao_dich=trans_id
       )


   return {"resultCode": 0, "message": "Confirmed"}, 200

# =========================================================
# CHỈNH SỬA THÔNG TIN CƠ BẢN KHÁCH SẠN
# =========================================================
@app.route("/quan-ly/khach-san/<int:hotel_id>/chinh-sua", methods=["POST"])
@owner_required
def chinh_sua_khach_san(hotel_id):
    user_id = session.get("user_id")

    if not is_hotel_belong_to_owner(hotel_id, user_id):
        flash("Bạn không có quyền chỉnh sửa khách sạn này.", "error")
        return redirect(url_for("chu_khach_san_dashboard"))

    ten_khach_san = request.form.get("ten_khach_san", "").strip()
    thanh_pho = request.form.get("thanh_pho", "").strip()
    dia_chi = request.form.get("dia_chi", "").strip()

    if not ten_khach_san or not thanh_pho or not dia_chi:
        flash("Vui lòng nhập đầy đủ thông tin.", "error")
        return redirect(url_for("chu_khach_san_dashboard"))

    success, result = update_hotel_basic_info(hotel_id, ten_khach_san, thanh_pho, dia_chi)

    if success:
        if result["can_duyet_lai"]:
            flash(
                "Cập nhật thành công! Khách sạn đã được chuyển về trạng thái chờ duyệt lại vì bạn đã thay đổi thông tin quan trọng.",
                "warning"
            )
        else:
            flash("Cập nhật khách sạn thành công.", "success")
    else:
        flash(result, "error")

    return redirect(url_for("chu_khach_san_dashboard"))


# ROUTE: CHI TIẾT ĐƠN ĐẶT PHÒNG (KHÁCH HÀNG)
@app.route("/don-dat-phong/<int:booking_id>")
@login_required
def chi_tiet_don_khach_hang(booking_id):
    user_id = session.get("user_id")
    booking = get_booking_detail_for_customer(booking_id, user_id)

    if not booking:
        flash("Không tìm thấy đơn đặt phòng.", "error")
        return redirect(url_for("ho_so"))

    can_cancel, _ = kiem_tra_co_the_huy_don(booking_id, user_id)

    chinh_sach_map = {0: "Trước 1 ngày", 1: "Trước 3 ngày", 2: "Không cho hủy"}
    chinh_sach_huy_text = chinh_sach_map.get(booking.khach_san.ChinhSachHuy, "Không xác định")

    return render_template(
        "ChiTietDonKhachHang.html",
        booking=booking,
        can_cancel=can_cancel,
        chinh_sach_huy_text=chinh_sach_huy_text
    )


# ROUTE: HỦY ĐƠN (KHÁCH HÀNG)
@app.route("/don-dat-phong/<int:booking_id>/huy", methods=["POST"])
@login_required
def huy_don_khach_hang(booking_id):
    user_id = session.get("user_id")
    ly_do_huy = request.form.get("ly_do_huy", "").strip()

    success, message = huy_don_boi_khach_hang(booking_id, user_id, ly_do_huy or None)

    flash(message, "success" if success else "error")
    return redirect(url_for("chi_tiet_don_khach_hang", booking_id=booking_id))

import hmac
import hashlib
import json
import requests
from datetime import datetime

MOMO_ENDPOINT = "https://test-payment.momo.vn/v2/gateway/api/create"

MOMO_PARTNER_CODE = "MOMOBKUN20180529"
MOMO_ACCESS_KEY = "F9A2..."
MOMO_SECRET_KEY = "S8K..."

if __name__ == "__main__":
    app.run(debug=True)