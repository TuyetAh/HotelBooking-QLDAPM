import os
from sqlalchemy import and_
from datetime import date, timedelta, time
from sqlalchemy import func
from werkzeug.utils import secure_filename
import shutil
from datetime import datetime
from decimal import Decimal
import math

from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask import current_app
import uuid

from app import db
from app.models import (
    NguoiDung,
    ChuKhachSan,
    KhachSan,
    TienIch,
    TienIchKhachSan,
    LoaiPhong,
    TienIchLoaiPhong,
    DatPhong,
    ChiTietDatPhong,
    ThanhToan,
    HoanTien,
    DanhGia,
    ChuyenTienKhachSan
)

# =========================================================
# 1. HẰNG SỐ / MAPPING HIỂN THỊ
# =========================================================

VAI_TRO_TEXT = {
    0: "Quản trị viên",
    1: "Chủ khách sạn",
    2: "Khách hàng"
}

TRANG_THAI_HOAT_DONG_TEXT = {
    0: "Dừng hoạt động",
    1: "Đang hoạt động"
}

CHINH_SACH_HUY_TEXT = {
    0: "Trước 1 ngày",
    1: "Trước 3 ngày",
    2: "Không cho hủy"
}

TRANG_THAI_DUYET_TEXT = {
    0: "Chờ duyệt",
    1: "Đã duyệt",
    2: "Từ chối"
}

TRANG_THAI_DAT_PHONG_TEXT = {
    0: "Chờ thanh toán",
    1: "Đã thanh toán",
    2: "Đã hủy",
    3: "Hoàn thành"
}

TRANG_THAI_THANH_TOAN_TEXT = {
    0: "Chờ thanh toán",
    1: "Thành công",
    2: "Thất bại",
    3: "Đã hoàn tiền"
}

TRANG_THAI_HOAN_TIEN_TEXT = {
    0: "Chờ xử lý",
    1: "Thành công",
    2: "Thất bại"
}

TRANG_THAI_CHUYEN_TIEN_TEXT = {
    0: "Chờ chuyển tiền",
    1: "Đã chuyển",
    2: "Thất bại"
}

import unicodedata


def remove_vietnamese_accents(text):
    if not text:
        return ""

    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    text = text.replace("Đ", "D").replace("đ", "d")
    return text


def normalize_search_keyword(keyword):
    """
    Chuẩn hóa:
    - viết hoa/thường
    - có dấu/không dấu
    - viết liền/viết cách
    """
    if not keyword:
        return ""

    keyword = keyword.strip().lower()
    keyword = remove_vietnamese_accents(keyword)

    # bỏ các ký tự dễ gây lệch
    keyword = keyword.replace(".", "")
    keyword = keyword.replace("-", "")
    keyword = keyword.replace("_", "")
    keyword = " ".join(keyword.split())

    # xử lý các tên đặc biệt
    keyword_no_space = keyword.replace(" ", "")

    # TP Hồ Chí Minh
    hcm_aliases = [
        "tphochiminh",
        "thanhphohochiminh",
        "hochiminh",
        "hcm",
        "sg",
        "saigon",
        "sai gon"
    ]

    if keyword_no_space in hcm_aliases or keyword in hcm_aliases:
        return "ho chi minh"

    # Đà Lạt
    if keyword_no_space in ["dalat", "da lat"]:
        return "da lat"

    # Đà Nẵng
    if keyword_no_space in ["danang", "da nang"]:
        return "da nang"

    # Nha Trang
    if keyword_no_space in ["nhatrang", "nha trang"]:
        return "nha trang"

    # Hà Nội
    if keyword_no_space in ["hanoi", "ha noi"]:
        return "ha noi"

    return keyword
# =========================================================
# 2. HÀM HỖ TRỢ HIỂN THỊ TEXT
# =========================================================

def hien_thi_vai_tro(value):
    return VAI_TRO_TEXT.get(value, "Không xác định")


def hien_thi_trang_thai_hoat_dong(value):
    return TRANG_THAI_HOAT_DONG_TEXT.get(value, "Không xác định")


def hien_thi_chinh_sach_huy(value):
    return CHINH_SACH_HUY_TEXT.get(value, "Không xác định")


def hien_thi_trang_thai_duyet(value):
    return TRANG_THAI_DUYET_TEXT.get(value, "Không xác định")


def hien_thi_trang_thai_dat_phong(value):
    return TRANG_THAI_DAT_PHONG_TEXT.get(value, "Không xác định")


def hien_thi_trang_thai_thanh_toan(value):
    return TRANG_THAI_THANH_TOAN_TEXT.get(value, "Không xác định")


def hien_thi_trang_thai_hoan_tien(value):
    return TRANG_THAI_HOAN_TIEN_TEXT.get(value, "Không xác định")


def hien_thi_trang_thai_chuyen_tien(value):
    return TRANG_THAI_CHUYEN_TIEN_TEXT.get(value, "Không xác định")


# =========================================================
# 3. HÀM HỖ TRỢ XỬ LÝ ẢNH TỪ THƯ MỤC
#
# ThuMucAnh trong DB ví dụ:
# - khachsan/ks_1
# - loaiphong/lp_1
#
# Đường dẫn thật:
# app/static/images/khachsan/ks_1
# =========================================================

def lay_duong_dan_thu_muc_anh(relative_folder):
    """
    Chuyển ThuMucAnh trong DB thành đường dẫn tuyệt đối trong project.

    Ví dụ:
    relative_folder = 'khachsan/ks_1'

    Kết quả:
    .../app/static/images/khachsan/ks_1
    """
    if not relative_folder:
        return None

    return os.path.join(current_app.root_path, "static", "images", relative_folder)


def lay_danh_sach_anh_va_loi(relative_folder):
    """
    Trả về:
        (danh_sach_anh, thong_bao_loi)

    danh_sach_anh: list dùng cho url_for('static', filename=...)
    ví dụ:
        ['images/khachsan/ks_1/1.jpg', 'images/khachsan/ks_1/2.jpg']

    thong_bao_loi:
        None nếu không lỗi
        chuỗi mô tả nếu có vấn đề
    """
    if not relative_folder:
        return [], "Khách sạn chưa có ThuMucAnh trong database"

    folder_path = lay_duong_dan_thu_muc_anh(relative_folder)

    if not folder_path:
        return [], "Không tạo được đường dẫn thư mục ảnh"

    if not os.path.exists(folder_path):
        return [], f"Không tìm thấy thư mục ảnh: {folder_path}"

    if not os.path.isdir(folder_path):
        return [], f"Đường dẫn không phải thư mục: {folder_path}"

    valid_extensions = (".png", ".jpg", ".jpeg", ".webp", ".gif")
    image_files = []

    for file_name in os.listdir(folder_path):
        full_file_path = os.path.join(folder_path, file_name)

        if os.path.isfile(full_file_path) and file_name.lower().endswith(valid_extensions):
            image_files.append(file_name)

    image_files.sort()

    if not image_files:
        return [], f"Thư mục có tồn tại nhưng không có file ảnh hợp lệ: {folder_path}"

    result = [f"images/{relative_folder}/{file_name}" for file_name in image_files]
    return result, None

def lay_danh_sach_anh(relative_folder):
    ds_anh, _ = lay_danh_sach_anh_va_loi(relative_folder)
    return ds_anh


def lay_anh_dau_tien_va_loi(relative_folder):
    """
    Trả về:
        (anh_dau_tien, thong_bao_loi)
    """
    ds_anh, loi = lay_danh_sach_anh_va_loi(relative_folder)

    if ds_anh:
        return ds_anh[0], None

    return None, loi


def lay_anh_dau_tien(relative_folder):
    anh, _ = lay_anh_dau_tien_va_loi(relative_folder)
    return anh






def xoa_thu_muc_anh(relative_folder):
    """
    Xóa cả thư mục ảnh khi admin từ chối hoặc khi cần dọn dữ liệu.
    """
    if not relative_folder:
        return False

    folder_path = lay_duong_dan_thu_muc_anh(relative_folder)

    if folder_path and os.path.exists(folder_path):
        shutil.rmtree(folder_path)
        return True

    return False


# =========================================================
# 4. NGƯỜI DÙNG / ĐĂNG NHẬP / ĐĂNG KÝ
# =========================================================

def get_user_by_id(user_id):
    return NguoiDung.query.get(user_id)


def get_user_by_username(username):
    return NguoiDung.query.filter_by(TenDangNhap=username).first()


def get_user_by_email(email):
    return NguoiDung.query.filter_by(Email=email).first()


def check_login(username, password):
    user = NguoiDung.query.filter_by(TenDangNhap=username).first()

    if not user:
        return None

    if user.TrangThaiHoatDong != 1:
        return None

    try:
        if check_password_hash(user.MatKhau, password):
            return user
    except Exception:
        pass

    if user.MatKhau == password:
        return user

    return None


def register_user(ten_dang_nhap, mat_khau, ho_ten, so_dien_thoai, email,
                  so_tai_khoan_ngan_hang=None, vai_tro=2):
    if get_user_by_username(ten_dang_nhap):
        return False, "Tên đăng nhập đã tồn tại"

    if get_user_by_email(email):
        return False, "Email đã được sử dụng"

    hashed_password = generate_password_hash(mat_khau)

    new_user = NguoiDung(
        TenDangNhap=ten_dang_nhap,
        MatKhau=hashed_password,
        HoTen=ho_ten,
        SoDienThoai=so_dien_thoai,
        Email=email,
        SoTaiKhoanNganHang=so_tai_khoan_ngan_hang,
        VaiTro=vai_tro,
        TrangThaiHoatDong=1
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        return True, new_user
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi đăng ký: {str(e)}"


def create_hotel_owner_account(ten_dang_nhap, mat_khau, ho_ten, so_dien_thoai,
                               email, so_tai_khoan_ngan_hang=None,
                               ten_doanh_nghiep=None, dia_chi_doanh_nghiep=None):
    if get_user_by_username(ten_dang_nhap):
        return False, "Tên đăng nhập đã tồn tại"

    if get_user_by_email(email):
        return False, "Email đã được sử dụng"

    hashed_password = generate_password_hash(mat_khau)

    try:
        owner_user = NguoiDung(
            TenDangNhap=ten_dang_nhap,
            MatKhau=hashed_password,
            HoTen=ho_ten,
            SoDienThoai=so_dien_thoai,
            Email=email,
            SoTaiKhoanNganHang=so_tai_khoan_ngan_hang,
            VaiTro=1,
            TrangThaiHoatDong=1
        )
        db.session.add(owner_user)
        db.session.flush()

        owner_info = ChuKhachSan(
            MaNguoiDung=owner_user.MaNguoiDung,
            TenDoanhNghiep=ten_doanh_nghiep,
            DiaChiDoanhNghiep=dia_chi_doanh_nghiep
        )
        db.session.add(owner_info)

        db.session.commit()
        return True, owner_user
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi tạo tài khoản chủ khách sạn: {str(e)}"


def is_admin(user):
    return user is not None and user.VaiTro == 0


def is_hotel_owner(user):
    return user is not None and user.VaiTro == 1


def is_customer(user):
    return user is not None and user.VaiTro == 2

def is_hotel_belong_to_owner(hotel_id, user_id):
    hotel = KhachSan.query.join(
        ChuKhachSan,
        KhachSan.MaChuKhachSan == ChuKhachSan.MaChuKhachSan
    ).filter(
        KhachSan.MaKhachSan == hotel_id,
        ChuKhachSan.MaNguoiDung == user_id
    ).first()

    return hotel is not None

# =========================================================
# 5. KHÁCH SẠN
# =========================================================

def get_all_hotels():
    """
    Lấy tất cả khách sạn đã duyệt và đang hoạt động.
    """
    return KhachSan.query.filter(
        KhachSan.TrangThaiDuyet == 1,
        KhachSan.TrangThaiHoatDong == 1
    ).order_by(KhachSan.NgayTao.desc()).all()


def get_featured_hotels(limit=6):
    """
    Lấy khách sạn nổi bật.
    """
    return KhachSan.query.filter(
        KhachSan.TrangThaiDuyet == 1,
        KhachSan.TrangThaiHoatDong == 1
    ).order_by(
        KhachSan.DiemDanhGiaTrungBinh.desc(),
        KhachSan.NgayTao.desc()
    ).limit(limit).all()


def get_hotel_by_id(hotel_id):
    return KhachSan.query.get(hotel_id)


def get_hotels_by_city(city_name):
    return KhachSan.query.filter(
        KhachSan.ThanhPho.ilike(f"%{city_name}%"),
        KhachSan.TrangThaiDuyet == 1,
        KhachSan.TrangThaiHoatDong == 1
    ).all()


def search_hotels(keyword=None, city=None):
    """
    Tìm kiếm khách sạn theo từ khóa / thành phố.
    """
    query = KhachSan.query.filter(
        KhachSan.TrangThaiDuyet == 1,
        KhachSan.TrangThaiHoatDong == 1
    )

    if keyword:
        query = query.filter(
            or_(
                KhachSan.TenKhachSan.ilike(f"%{keyword}%"),
                KhachSan.DiaChi.ilike(f"%{keyword}%"),
                KhachSan.ViTriNoiBat.ilike(f"%{keyword}%")
            )
        )

    if city:
        query = query.filter(KhachSan.ThanhPho.ilike(f"%{city}%"))

    return query.order_by(KhachSan.NgayTao.desc()).all()


def create_hotel(ma_chu_khach_san, ten_khach_san, thanh_pho, dia_chi,
                 vi_tri_noi_bat, so_dien_thoai_lien_he, mo_ta,
                 quy_dinh_khach_san, chinh_sach_huy, thu_muc_anh=None):
    """
    Tạo khách sạn mới ở trạng thái chờ duyệt.
    """
    new_hotel = KhachSan(
        MaChuKhachSan=ma_chu_khach_san,
        TenKhachSan=ten_khach_san,
        ThanhPho=thanh_pho,
        DiaChi=dia_chi,
        ViTriNoiBat=vi_tri_noi_bat,
        SoDienThoaiLienHe=so_dien_thoai_lien_he,
        MoTa=mo_ta,
        QuyDinhKhachSan=quy_dinh_khach_san,
        ChinhSachHuy=chinh_sach_huy,
        ThuMucAnh=thu_muc_anh,
        TrangThaiDuyet=0,
        TrangThaiHoatDong=1
    )

    try:
        db.session.add(new_hotel)
        db.session.commit()
        return True, new_hotel
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi tạo khách sạn: {str(e)}"


def update_hotel(hotel_id, **kwargs):
    """
    Cập nhật thông tin khách sạn.
    """
    hotel = get_hotel_by_id(hotel_id)
    if not hotel:
        return False, "Không tìm thấy khách sạn"

    allowed_fields = [
        "TenKhachSan", "ThanhPho", "DiaChi", "ViTriNoiBat",
        "SoDienThoaiLienHe", "MoTa", "QuyDinhKhachSan",
        "ChinhSachHuy", "ThuMucAnh", "TrangThaiHoatDong"
    ]

    for field, value in kwargs.items():
        if field in allowed_fields:
            setattr(hotel, field, value)

    hotel.NgayCapNhat = datetime.now()

    try:
        db.session.commit()
        return True, hotel
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi cập nhật khách sạn: {str(e)}"


def get_hotel_images(hotel):
    """
    Lấy danh sách ảnh của khách sạn từ ThuMucAnh.
    """
    if not hotel:
        return []
    return lay_danh_sach_anh(hotel.ThuMucAnh)


def get_hotel_cover_image(hotel):
    """
    Lấy ảnh đầu tiên của khách sạn.
    """
    if not hotel:
        return None
    return lay_anh_dau_tien(hotel.ThuMucAnh)


def get_hotel_detail_data(hotel_id, checkin=None, checkout=None, so_nguoi_lon=None, so_phong=1):
    hotel = get_hotel_by_id(hotel_id)
    if not hotel:
        return None

    images = lay_danh_sach_anh(hotel.ThuMucAnh)

    checkin_date = None
    checkout_date = None

    try:
        if checkin:
            checkin_date = datetime.strptime(checkin, "%Y-%m-%d").date()
        if checkout:
            checkout_date = datetime.strptime(checkout, "%Y-%m-%d").date()
    except Exception:
        checkin_date = None
        checkout_date = None

    so_phong_can = int(so_phong) if so_phong not in (None, "") else 1
    so_nguoi_can = int(so_nguoi_lon) if so_nguoi_lon not in (None, "") else None

    available_rooms_data = get_available_room_types_by_hotel(
        hotel_id=hotel.MaKhachSan,
        checkin=checkin_date,
        checkout=checkout_date,
        so_phong_can=so_phong_can,
        so_nguoi_lon=so_nguoi_can
    )

    room_cards = []
    all_images = []

    # ảnh khách sạn
    for img in images:
        all_images.append({
            "url": img,
            "type": "Khách sạn",
            "name": hotel.TenKhachSan
        })

    # ảnh loại phòng
    for room_item in room_cards:
        room = room_item["room"]
        for img in room_item["images"]:
            all_images.append({
                "url": img,
                "type": "Loại phòng",
                "name": room.TenLoaiPhong
            })

    for item in available_rooms_data:
        room = item["room"]
        room_cards.append({
            "room": room,
            "so_phong_con_trong": item["so_phong_con_trong"],
            "images": lay_danh_sach_anh(room.ThuMucAnh),
            "cover_image": lay_anh_dau_tien(room.ThuMucAnh),
            "tien_ichs": room.tien_ichs
        })

    min_price = None
    if room_cards:
        min_price = min(item["room"].GiaMoiDem for item in room_cards)

    return {
        "hotel": hotel,
        "images": images,
        "all_images": all_images,
        "cover_image": images[0] if images else None,
        "room_cards": room_cards,
        "reviews": get_reviews_by_hotel(hotel_id),
        "review_count": get_review_count_by_hotel(hotel_id),
        "tien_ichs": hotel.tien_ichs,
        "min_price": min_price,
        "chinh_sach_huy_text": hien_thi_chinh_sach_huy(hotel.ChinhSachHuy),
        "checkin": checkin,
        "checkout": checkout,
        "so_nguoi_lon": so_nguoi_lon or 2,
        "so_phong": so_phong or 1
    }





# =========================================================
# 6. LOẠI PHÒNG
# =========================================================

def get_room_type_by_id(room_type_id):
    return LoaiPhong.query.get(room_type_id)


def get_room_types_by_hotel(hotel_id):
    return LoaiPhong.query.filter_by(
        MaKhachSan=hotel_id,
        TrangThaiHoatDong=1
    ).all()


def create_room_type(ma_khach_san, ten_loai_phong, mo_ta,
                     gia_moi_dem, so_nguoi_toi_da, so_luong_phong,
                     thu_muc_anh=None):
    """
    Tạo loại phòng.
    """
    room_type = LoaiPhong(
        MaKhachSan=ma_khach_san,
        TenLoaiPhong=ten_loai_phong,
        MoTa=mo_ta,
        GiaMoiDem=gia_moi_dem,
        SoNguoiToiDa=so_nguoi_toi_da,
        SoLuongPhong=so_luong_phong,
        ThuMucAnh=thu_muc_anh,
        TrangThaiHoatDong=1
    )

    try:
        db.session.add(room_type)
        db.session.commit()
        return True, room_type
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi tạo loại phòng: {str(e)}"


def update_room_type(room_type_id, **kwargs):
    room_type = get_room_type_by_id(room_type_id)
    if not room_type:
        return False, "Không tìm thấy loại phòng"

    allowed_fields = [
        "TenLoaiPhong", "MoTa", "GiaMoiDem",
        "SoNguoiToiDa", "SoLuongPhong",
        "ThuMucAnh", "TrangThaiHoatDong"
    ]

    for field, value in kwargs.items():
        if field in allowed_fields:
            setattr(room_type, field, value)

    room_type.NgayCapNhat = datetime.now()

    try:
        db.session.commit()
        return True, room_type
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi cập nhật loại phòng: {str(e)}"


def get_room_images(room_type):
    if not room_type:
        return []
    return lay_danh_sach_anh(room_type.ThuMucAnh)


def get_room_cover_image(room_type):
    if not room_type:
        return None
    return lay_anh_dau_tien(room_type.ThuMucAnh)


# =========================================================
# 7. TIỆN ÍCH
# =========================================================

def get_all_tien_ich():
    return TienIch.query.order_by(TienIch.TenTienIch.asc()).all()


def add_tien_ich_to_hotel(ma_khach_san, ma_tien_ich):
    existing = TienIchKhachSan.query.filter_by(
        MaKhachSan=ma_khach_san,
        MaTienIch=ma_tien_ich
    ).first()

    if existing:
        return False, "Tiện ích đã tồn tại trong khách sạn"

    item = TienIchKhachSan(
        MaKhachSan=ma_khach_san,
        MaTienIch=ma_tien_ich
    )

    try:
        db.session.add(item)
        db.session.commit()
        return True, item
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi thêm tiện ích khách sạn: {str(e)}"


def add_tien_ich_to_room_type(ma_loai_phong, ma_tien_ich):
    existing = TienIchLoaiPhong.query.filter_by(
        MaLoaiPhong=ma_loai_phong,
        MaTienIch=ma_tien_ich
    ).first()

    if existing:
        return False, "Tiện ích đã tồn tại trong loại phòng"

    item = TienIchLoaiPhong(
        MaLoaiPhong=ma_loai_phong,
        MaTienIch=ma_tien_ich
    )

    try:
        db.session.add(item)
        db.session.commit()
        return True, item
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi thêm tiện ích loại phòng: {str(e)}"


# =========================================================
# 8. REVIEW / ĐÁNH GIÁ
# =========================================================

def get_reviews_by_hotel(hotel_id):
    return DanhGia.query.filter_by(
        MaKhachSan=hotel_id
    ).order_by(DanhGia.NgayDanhGia.desc()).all()


def get_review_count_by_hotel(hotel_id):
    return DanhGia.query.filter_by(MaKhachSan=hotel_id).count()





# =========================================================
# 9. ĐẶT PHÒNG
# =========================================================

def get_booking_by_id(booking_id):
    return DatPhong.query.get(booking_id)


def get_bookings_by_user(user_id):
    return DatPhong.query.filter_by(MaNguoiDung=user_id).order_by(
        DatPhong.NgayTao.desc()
    ).all()


# =========================================================
# 10. THANH TOÁN
# =========================================================

def get_payment_by_booking_id(booking_id):
    return ThanhToan.query.filter_by(MaDatPhong=booking_id).first()


def create_payment(ma_dat_phong, phuong_thuc_thanh_toan,
                   trang_thai_thanh_toan, so_tien_thanh_toan,
                   ma_giao_dich=None, thoi_gian_thanh_toan=None):
    """
    Tạo thanh toán cho đơn.
    """
    existing_payment = get_payment_by_booking_id(ma_dat_phong)
    if existing_payment:
        return False, "Đơn đặt phòng này đã có thanh toán"

    payment = ThanhToan(
        MaDatPhong=ma_dat_phong,
        PhuongThucThanhToan=phuong_thuc_thanh_toan,
        TrangThaiThanhToan=trang_thai_thanh_toan,
        SoTienThanhToan=so_tien_thanh_toan,
        MaGiaoDich=ma_giao_dich,
        ThoiGianThanhToan=thoi_gian_thanh_toan
    )

    try:
        db.session.add(payment)

        booking = get_booking_by_id(ma_dat_phong)
        if booking and trang_thai_thanh_toan == 1:
            booking.TrangThaiDatPhong = 1

        db.session.commit()
        return True, payment
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi tạo thanh toán: {str(e)}"


# =========================================================
# 11. HOÀN TIỀN
# =========================================================

def get_refund_by_booking_id(booking_id):
    return HoanTien.query.filter_by(MaDatPhong=booking_id).first()


def create_refund(ma_dat_phong, so_tien_hoan, ly_do_hoan_tien=None,
                  trang_thai_hoan_tien=0, thoi_gian_hoan_tien=None):
    existing_refund = get_refund_by_booking_id(ma_dat_phong)
    if existing_refund:
        return False, "Đơn đặt phòng này đã có bản ghi hoàn tiền"

    refund = HoanTien(
        MaDatPhong=ma_dat_phong,
        SoTienHoan=so_tien_hoan,
        LyDoHoanTien=ly_do_hoan_tien,
        TrangThaiHoanTien=trang_thai_hoan_tien,
        ThoiGianHoanTien=thoi_gian_hoan_tien
    )

    try:
        db.session.add(refund)
        db.session.commit()
        return True, refund
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi tạo hoàn tiền: {str(e)}"


# =========================================================
# 12. CHUYỂN TIỀN CHO KHÁCH SẠN
# =========================================================

def get_transfer_by_booking_id(booking_id):
    return ChuyenTienKhachSan.query.filter_by(MaDatPhong=booking_id).first()


def create_transfer_to_hotel(ma_dat_phong, ma_khach_san, tong_tien_don_hang,
                             phi_he_thong, so_tien_chuyen_cho_khach_san,
                             trang_thai_chuyen_tien=0, thoi_gian_chuyen_tien=None):
    existing_transfer = get_transfer_by_booking_id(ma_dat_phong)
    if existing_transfer:
        return False, "Đơn đặt phòng này đã có bản ghi chuyển tiền"

    transfer = ChuyenTienKhachSan(
        MaDatPhong=ma_dat_phong,
        MaKhachSan=ma_khach_san,
        TongTienDonHang=tong_tien_don_hang,
        PhiHeThong=phi_he_thong,
        SoTienChuyenChoKhachSan=so_tien_chuyen_cho_khach_san,
        TrangThaiChuyenTien=trang_thai_chuyen_tien,
        ThoiGianChuyenTien=thoi_gian_chuyen_tien
    )

    try:
        db.session.add(transfer)
        db.session.commit()
        return True, transfer
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi tạo chuyển tiền: {str(e)}"


# =========================================================
# 13. HÀM CHO ADMIN
# =========================================================

def get_pending_hotels():
    """
    Lấy danh sách khách sạn chờ duyệt.
    """
    return KhachSan.query.filter_by(TrangThaiDuyet=0).order_by(
        KhachSan.NgayTao.desc()
    ).all()


def get_rejected_hotels():
    return KhachSan.query.filter_by(TrangThaiDuyet=2).order_by(
        KhachSan.NgayTao.desc()
    ).all()


def approve_hotel(hotel_id):
    hotel = get_hotel_by_id(hotel_id)
    if not hotel:
        return False, "Không tìm thấy khách sạn"

    hotel.TrangThaiDuyet = 1
    hotel.NgayDuyet = datetime.now()
    hotel.LyDoTuChoi = None

    try:
        db.session.commit()
        return True, hotel
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi duyệt khách sạn: {str(e)}"


def reject_hotel(hotel_id, ly_do_tu_choi=None, xoa_anh=True):
    """
    Từ chối khách sạn.
    Nếu xoa_anh=True thì xóa thư mục ảnh của khách sạn và cả loại phòng thuộc khách sạn.
    """
    hotel = get_hotel_by_id(hotel_id)
    if not hotel:
        return False, "Không tìm thấy khách sạn"

    try:
        # Xóa ảnh loại phòng
        if xoa_anh:
            for room in hotel.loai_phongs:
                if room.ThuMucAnh:
                    xoa_thu_muc_anh(room.ThuMucAnh)

            # Xóa ảnh khách sạn
            if hotel.ThuMucAnh:
                xoa_thu_muc_anh(hotel.ThuMucAnh)

        hotel.TrangThaiDuyet = 2
        hotel.LyDoTuChoi = ly_do_tu_choi
        hotel.NgayDuyet = None

        db.session.commit()
        return True, hotel
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi từ chối khách sạn: {str(e)}"


def suspend_hotel(hotel_id):
    """
    Dừng hoạt động khách sạn.
    """
    hotel = get_hotel_by_id(hotel_id)
    if not hotel:
        return False, "Không tìm thấy khách sạn"

    hotel.TrangThaiHoatDong = 0

    try:
        db.session.commit()
        return True, hotel
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi dừng hoạt động khách sạn: {str(e)}"


def activate_hotel(hotel_id):
    """
    Kích hoạt lại khách sạn.
    """
    hotel = get_hotel_by_id(hotel_id)
    if not hotel:
        return False, "Không tìm thấy khách sạn"

    hotel.TrangThaiHoatDong = 1

    try:
        db.session.commit()
        return True, hotel
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi kích hoạt khách sạn: {str(e)}"


# =========================================================
# 14. HÀM HỖ TRỢ TRẢ DỮ LIỆU CHO TEMPLATE
# =========================================================


def build_hotel_card_data(hotel, checkin=None, checkout=None, so_nguoi_lon=None, so_phong=1):
    """ếu có checkin/checkout thì giá hiển thị sẽ là giá thấp nhấttrong các loại phòng còn trống theo đúng khoảng ngày đang tìm.
    """
    if not hotel:
        return None

    images = lay_danh_sach_anh(hotel.ThuMucAnh)
    cover_image = images[0] if images else None

    image_error = None if images else "Khách sạn chưa có ảnh"

    checkin_date = None
    checkout_date = None

    try:
        if checkin:
            checkin_date = datetime.strptime(checkin, "%Y-%m-%d").date()
        if checkout:
            checkout_date = datetime.strptime(checkout, "%Y-%m-%d").date()
    except Exception:
        checkin_date = None
        checkout_date = None

    so_phong_can = int(so_phong) if so_phong not in (None, "",) else 1
    so_nguoi_can = int(so_nguoi_lon) if so_nguoi_lon not in (None, "",) else None

    # Nếu có ngày tìm kiếm thì lấy phòng còn trống thật sự
    if checkin_date and checkout_date:
        available_rooms_data = get_available_room_types_by_hotel(
            hotel_id=hotel.MaKhachSan,
            checkin=checkin_date,
            checkout=checkout_date,
            so_phong_can=so_phong_can,
            so_nguoi_lon=so_nguoi_can
        )
        available_rooms = [item["room"] for item in available_rooms_data]
    else:
        # Nếu chưa có ngày thì lấy phòng đang hoạt động bình thường
        available_rooms = [
            room for room in hotel.loai_phongs
            if room.TrangThaiHoatDong == 1
        ]

        if so_nguoi_can:
            available_rooms = [
                room for room in available_rooms
                if room.SoNguoiToiDa >= so_nguoi_can
            ]

        available_rooms = [
            room for room in available_rooms
            if room.SoLuongPhong >= so_phong_can
        ]

    min_price = None
    if available_rooms:
        min_price = min(room.GiaMoiDem for room in available_rooms)

    return {
        "hotel": hotel,
        "cover_image": cover_image,
        "images": images,
        "image_error": image_error,
        "thu_muc_anh": hotel.ThuMucAnh,
        "min_price": min_price,
        "available_rooms": available_rooms,
        "available_room_count": len(available_rooms),
        "chinh_sach_huy_text": hien_thi_chinh_sach_huy(hotel.ChinhSachHuy),
        "trang_thai_duyet_text": hien_thi_trang_thai_duyet(hotel.TrangThaiDuyet),
        "trang_thai_hoat_dong_text": hien_thi_trang_thai_hoat_dong(hotel.TrangThaiHoatDong),
        "review_count": get_review_count_by_hotel(hotel.MaKhachSan)
    }


def build_room_type_data(room_type):
    if not room_type:
        return None

    return {
        "room_type": room_type,
        "cover_image": get_room_cover_image(room_type),
        "images": get_room_images(room_type),
        "trang_thai_hoat_dong_text": hien_thi_trang_thai_hoat_dong(room_type.TrangThaiHoatDong)
    }


def build_booking_data(booking):
    if not booking:
        return None

    return {
        "booking": booking,
        "trang_thai_dat_phong_text": hien_thi_trang_thai_dat_phong(booking.TrangThaiDatPhong),
        "payment": booking.thanh_toan,
        "refund": booking.hoan_tien,
        "transfer": booking.chuyen_tien_khach_san
    }

def cap_nhat_thu_muc_anh_khach_san(ma_khach_san, thu_muc_anh):
    hotel = get_hotel_by_id(ma_khach_san)
    if not hotel:
        return False, "Không tìm thấy khách sạn"

    hotel.ThuMucAnh = thu_muc_anh
    hotel.NgayCapNhat = datetime.now()

    try:
        db.session.commit()
        return True, hotel
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi cập nhật thư mục ảnh khách sạn: {str(e)}"


def cap_nhat_thu_muc_anh_loai_phong(ma_loai_phong, thu_muc_anh):
    room = get_room_type_by_id(ma_loai_phong)
    if not room:
        return False, "Không tìm thấy loại phòng"

    room.ThuMucAnh = thu_muc_anh
    room.NgayCapNhat = datetime.now()

    try:
        db.session.commit()
        return True, room
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi cập nhật thư mục ảnh loại phòng: {str(e)}"

def get_featured_hotels(limit=None):
    """
    Lấy khách sạn nổi bật:
    - đã duyệt
    - đang hoạt động
    - điểm đánh giá > 8.5
    """
    query = KhachSan.query.filter(
        KhachSan.TrangThaiDuyet == 1,
        KhachSan.TrangThaiHoatDong == 1,
        KhachSan.DiemDanhGiaTrungBinh > 8.5
    ).order_by(
        KhachSan.DiemDanhGiaTrungBinh.desc(),
        KhachSan.NgayTao.desc()
    )

    if limit:
        return query.limit(limit).all()

    return query.all()

#Chinhsua------------------------
def update_user(user_id, ho_ten, so_dien_thoai, email, so_tai_khoan_ngan_hang):
    user = get_user_by_id(user_id)
    if not user:
        return False, "Không tìm thấy người dùng"

    # Kiểm tra email trùng với người khác
    existing = NguoiDung.query.filter(
        NguoiDung.Email == email,
        NguoiDung.MaNguoiDung != user_id
    ).first()
    if existing:
        return False, "Email đã được sử dụng bởi tài khoản khác"

    user.HoTen = ho_ten
    user.SoDienThoai = so_dien_thoai
    user.Email = email
    user.SoTaiKhoanNganHang = so_tai_khoan_ngan_hang
    user.NgayCapNhat = datetime.now()

    try:
        db.session.commit()
        return True, user
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi: {str(e)}"


def doi_mat_khau(user_id, mat_khau_cu, mat_khau_moi):
    user = get_user_by_id(user_id)
    if not user:
        return False, "Không tìm thấy người dùng"

    # Kiểm tra mật khẩu cũ
    try:
        if not check_password_hash(user.MatKhau, mat_khau_cu):
            if user.MatKhau != mat_khau_cu:
                return False, "Mật khẩu cũ không đúng"
    except Exception:
        if user.MatKhau != mat_khau_cu:
            return False, "Mật khẩu cũ không đúng"

    user.MatKhau = generate_password_hash(mat_khau_moi)
    user.NgayCapNhat = datetime.now()

    try:
        db.session.commit()
        return True, "Đổi mật khẩu thành công"
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi: {str(e)}"

def get_hotels_by_owner(user_id):
    """Lấy danh sách KS của chủ KS theo user_id."""
    chu_ks = ChuKhachSan.query.filter_by(MaNguoiDung=user_id).first()
    if not chu_ks:
        return []
    return KhachSan.query.filter_by(
        MaChuKhachSan=chu_ks.MaChuKhachSan
    ).order_by(KhachSan.NgayTao.desc()).all()

def get_all_tien_ich_khach_san():
    """Lấy tiện ích loại hotel."""
    return TienIch.query.order_by(TienIch.TenTienIch.asc()).all()


def create_hotel_full(user_id, ten_khach_san, thanh_pho, dia_chi,
                      vi_tri_noi_bat, so_dien_thoai_lien_he, mo_ta,
                      quy_dinh_khach_san, chinh_sach_huy, ds_tien_ich):
    """Tạo khách sạn + gắn tiện ích."""
    chu_ks = ChuKhachSan.query.filter_by(MaNguoiDung=user_id).first()
    if not chu_ks:
        return False, "Không tìm thấy thông tin chủ khách sạn"

    new_hotel = KhachSan(
        MaChuKhachSan=chu_ks.MaChuKhachSan,
        TenKhachSan=ten_khach_san,
        ThanhPho=thanh_pho,
        DiaChi=dia_chi,
        ViTriNoiBat=vi_tri_noi_bat,
        SoDienThoaiLienHe=so_dien_thoai_lien_he,
        MoTa=mo_ta,
        QuyDinhKhachSan=quy_dinh_khach_san,
        ChinhSachHuy=int(chinh_sach_huy),
        TrangThaiDuyet=0,
        TrangThaiHoatDong=1
    )

    try:
        db.session.add(new_hotel)
        db.session.flush()

        # Gắn tiện ích
        for ma_tien_ich in ds_tien_ich:
            item = TienIchKhachSan(
                MaKhachSan=new_hotel.MaKhachSan,
                MaTienIch=int(ma_tien_ich)
            )
            db.session.add(item)

        db.session.commit()
        return True, new_hotel
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi: {str(e)}"

from sqlalchemy import and_

#Dùng cho trang tìm kiếm và nút tìm kiếm ửo trnag chủ
def get_all_amenities():
    """
    Lấy toàn bộ tiện ích để render bộ lọc.
    """
    return TienIch.query.order_by(TienIch.TenTienIch.asc()).all()

def hotel_match_amenities(hotel, tien_ich_ids):
    if not tien_ich_ids:
        return True

    tien_ich_ids = [int(x) for x in tien_ich_ids]

    # kiểm tra tiện ích khách sạn
    hotel_amenity_ids = [t.MaTienIch for t in hotel.tien_ichs]

    # kiểm tra tiện ích loại phòng
    room_amenity_ids = []

    for room in hotel.loai_phongs:
        for tien_ich in room.tien_ichs:
            room_amenity_ids.append(tien_ich.MaTienIch)

    all_ids = set(hotel_amenity_ids + room_amenity_ids)

    # Chỉ cần khách sạn hoặc phòng có tiện ích được chọn là được
    return any(tien_ich_id in all_ids for tien_ich_id in tien_ich_ids)


def search_hotels_advanced(
    keyword=None,
    city=None,
    checkin=None,
    checkout=None,
    so_nguoi_lon=None,
    so_phong=None,
    gia_tu=None,
    gia_den=None,
    so_sao=None,
    tien_ich_ids=None,
    chinh_sach_huy=None,
    sort_by="goi_y",
):
    """
    Tìm kiếm khách sạn nâng cao.

    sort_by:
        - goi_y
        - gia_tang
        - gia_giam
        - diem_danh_gia
        - moi_nhat
    """
    query = KhachSan.query.filter(
        KhachSan.TrangThaiDuyet == 1,
        KhachSan.TrangThaiHoatDong == 1
    )

    if keyword:
        normalized_keyword = normalize_search_keyword(keyword)

        hotels_temp = query.all()
        matched_hotel_ids = []

        for hotel in hotels_temp:
            ten_khach_san = normalize_search_keyword(hotel.TenKhachSan)
            thanh_pho = normalize_search_keyword(hotel.ThanhPho)
            dia_chi = normalize_search_keyword(hotel.DiaChi)
            vi_tri_noi_bat = normalize_search_keyword(hotel.ViTriNoiBat)

            searchable_text = f"{ten_khach_san} {thanh_pho} {dia_chi} {vi_tri_noi_bat}"
            searchable_text_no_space = searchable_text.replace(" ", "")
            keyword_no_space = normalized_keyword.replace(" ", "")

            if (
                    normalized_keyword in searchable_text
                    or keyword_no_space in searchable_text_no_space
            ):
                matched_hotel_ids.append(hotel.MaKhachSan)

        query = query.filter(KhachSan.MaKhachSan.in_(matched_hotel_ids))

    if city:
        query = query.filter(KhachSan.ThanhPho.ilike(f"%{city}%"))

    if chinh_sach_huy is not None and chinh_sach_huy != "":
        query = query.filter(KhachSan.ChinhSachHuy == int(chinh_sach_huy))



    hotels = query.all()

    filtered_hotels = []

    checkin_date = None
    checkout_date = None

    try:
        if checkin:
            checkin_date = datetime.strptime(checkin, "%Y-%m-%d").date()
        if checkout:
            checkout_date = datetime.strptime(checkout, "%Y-%m-%d").date()
    except Exception:
        checkin_date = None
        checkout_date = None

    so_phong_can = int(so_phong) if so_phong not in (None, "",) else 1
    so_nguoi_can = int(so_nguoi_lon) if so_nguoi_lon not in (None, "",) else None

    for hotel in hotels:

        # Lọc tiện ích: kiểm tra cả tiện ích khách sạn và tiện ích loại phòng
        if tien_ich_ids:
            selected_ids = [int(x) for x in tien_ich_ids]

            hotel_amenity_ids = [t.MaTienIch for t in hotel.tien_ichs]

            room_amenity_ids = []
            for room in hotel.loai_phongs:
                for tien_ich in room.tien_ichs:
                    room_amenity_ids.append(tien_ich.MaTienIch)

            all_amenity_ids = set(hotel_amenity_ids + room_amenity_ids)

            if not all(tien_ich_id in all_amenity_ids for tien_ich_id in selected_ids):
                continue

        available_rooms_data = get_available_room_types_by_hotel(
            hotel_id=hotel.MaKhachSan,
            checkin=checkin_date,
            checkout=checkout_date,
            so_phong_can=so_phong_can,
            so_nguoi_lon=so_nguoi_can
        )

        if not available_rooms_data:
            continue

        available_rooms = [item["room"] for item in available_rooms_data]

        # Lọc theo giá dựa trên phòng còn trống
        min_price = min(room.GiaMoiDem for room in available_rooms)

        if gia_tu not in (None, ""):
            if min_price < Decimal(str(gia_tu)):
                continue

        if gia_den not in (None, ""):
            if min_price > Decimal(str(gia_den)):
                continue

        # Lọc theo mức đánh giá
        if so_sao not in (None, ""):
            so_sao_int = int(so_sao)
            if so_sao_int == 5 and hotel.DiemDanhGiaTrungBinh < 9:
                continue
            elif so_sao_int == 4 and hotel.DiemDanhGiaTrungBinh < 8:
                continue
            elif so_sao_int == 3 and hotel.DiemDanhGiaTrungBinh < 7:
                continue

        filtered_hotels.append(hotel)

    # Sắp xếp
    if sort_by == "gia_tang":
        filtered_hotels.sort(
            key=lambda h: min([room.GiaMoiDem for room in h.loai_phongs if room.TrangThaiHoatDong == 1], default=999999999)
        )
    elif sort_by == "gia_giam":
        filtered_hotels.sort(
            key=lambda h: min([room.GiaMoiDem for room in h.loai_phongs if room.TrangThaiHoatDong == 1], default=0),
            reverse=True
        )
    elif sort_by == "diem_danh_gia":
        filtered_hotels.sort(key=lambda h: h.DiemDanhGiaTrungBinh, reverse=True)
    elif sort_by == "moi_nhat":
        filtered_hotels.sort(key=lambda h: h.NgayTao, reverse=True)
    else:
        # gợi ý
        filtered_hotels.sort(
            key=lambda h: (h.DiemDanhGiaTrungBinh, h.NgayTao),
            reverse=True
        )

    return filtered_hotels


def is_valid_booking_status_for_availability(trang_thai_dat_phong):
    """
    Những trạng thái vẫn giữ chỗ phòng.
    0 = Chờ thanh toán
    1 = Đã thanh toán

    Không tính:
    2 = Đã hủy
    3 = Hoàn thành
    """
    return trang_thai_dat_phong in [0, 1]


def kiem_tra_trung_ngay(ngay_nhan_phong_cu, ngay_tra_phong_cu, checkin_moi, checkout_moi):
    """trả về true nếu 2 khoảng ngày bị trùng á"""
    return ngay_nhan_phong_cu < checkout_moi and ngay_tra_phong_cu > checkin_moi


def tinh_so_phong_da_dat(ma_loai_phong, checkin, checkout):
    """chỉ tính các đơn còn giữ phòng:0 = chờ thanh toán va1 = dã thanh toán"""
    if not checkin or not checkout:
        return 0

    chi_tiet_dat_phongs = ChiTietDatPhong.query.filter_by(MaLoaiPhong=ma_loai_phong).all()
    tong_so_phong_da_dat = 0

    for chi_tiet in chi_tiet_dat_phongs:
        dat_phong = chi_tiet.dat_phong

        if not dat_phong:
            continue

        # chỉ tính đơn còn giữ chỗ
        if dat_phong.TrangThaiDatPhong not in [0, 1]:
            continue

        # nếu trùng lịch thì cộng vào
        if kiem_tra_trung_ngay(
            dat_phong.NgayNhanPhong,
            dat_phong.NgayTraPhong,
            checkin,
            checkout
        ):
            tong_so_phong_da_dat += chi_tiet.SoLuongPhongDat

    return tong_so_phong_da_dat


def tinh_so_phong_con_trong(loai_phong, checkin, checkout):
    """
    số phòng còn trống = tổng số phòng - số phòng đã bị đặt trong khoảng ngày trùng nhau"""
    if not loai_phong:
        return 0

    if not checkin or not checkout:
        return loai_phong.SoLuongPhong

    so_phong_da_dat = tinh_so_phong_da_dat(loai_phong.MaLoaiPhong, checkin, checkout)
    so_phong_con_trong = loai_phong.SoLuongPhong - so_phong_da_dat

    return max(0, so_phong_con_trong)


def get_available_room_types_by_hotel(hotel_id, checkin=None, checkout=None, so_phong_can=1, so_nguoi_lon=None):
    """
    Lấy các loại phòng còn trống của khách sạn trong khoảng ngày.
    """
    room_types = LoaiPhong.query.filter_by(
        MaKhachSan=hotel_id,
        TrangThaiHoatDong=1
    ).all()

    available_rooms = []

    for room in room_types:
        # Lọc theo sức chứa
        if so_nguoi_lon and room.SoNguoiToiDa < int(so_nguoi_lon):
            continue

        so_phong_con_trong = tinh_so_phong_con_trong(room, checkin, checkout)

        if so_phong_con_trong >= int(so_phong_can):
            available_rooms.append({
                "room": room,
                "so_phong_con_trong": so_phong_con_trong
            })

    return available_rooms
def get_room_booking_data(hotel_id, room_id, checkin, checkout, so_nguoi_lon=2, so_phong=1):
    hotel = get_hotel_by_id(hotel_id)
    room = get_room_type_by_id(room_id)

    if not hotel or not room:
        return None

    checkin_date = datetime.strptime(checkin, "%Y-%m-%d").date()
    checkout_date = datetime.strptime(checkout, "%Y-%m-%d").date()

    so_dem = (checkout_date - checkin_date).days
    so_phong = int(so_phong)

    tong_tien_phong = room.GiaMoiDem * so_dem * so_phong
    phi_dich_vu = tong_tien_phong * Decimal("0.10")
    tong_tien = tong_tien_phong
    so_phong_con_trong = tinh_so_phong_con_trong(room, checkin_date, checkout_date)

    return {
        "hotel": hotel,
        "room": room,
        "hotel_images": lay_danh_sach_anh(hotel.ThuMucAnh),
        "room_images": lay_danh_sach_anh(room.ThuMucAnh),
        "checkin": checkin,
        "checkout": checkout,
        "so_dem": so_dem,
        "so_nguoi_lon": so_nguoi_lon,
        "so_phong": so_phong,
        "so_phong_con_trong": so_phong_con_trong,
        "tong_tien_phong": tong_tien_phong,
        "phi_dich_vu": phi_dich_vu,
        "tong_tien": tong_tien,
        "chinh_sach_huy_text": hien_thi_chinh_sach_huy(hotel.ChinhSachHuy)
    }
def generate_booking_code():
   last_booking = DatPhong.query.order_by(DatPhong.MaDatPhong.desc()).first()


   if not last_booking or not last_booking.MaDatPhongCode:
       return "DP001"


   try:
       number = int(last_booking.MaDatPhongCode.replace("DP", ""))
   except:
       number = last_booking.MaDatPhong  # fallback


   return f"DP{number + 1:03d}"
def create_pending_booking(user_id, hotel_id, room_id, checkin, checkout, so_nguoi_luu_tru, so_phong):
   room = LoaiPhong.query.get(room_id)


   if not room:
       return False, "Không tìm thấy loại phòng."


   checkin_date = datetime.strptime(checkin, "%Y-%m-%d").date()
   checkout_date = datetime.strptime(checkout, "%Y-%m-%d").date()


   so_dem = (checkout_date - checkin_date).days


   if so_dem < 1:
       return False, "Ngày trả phòng phải sau ngày nhận phòng ít nhất 1 ngày."


   # kiểm tra phòng còn trống
   so_da_dat = tinh_so_phong_da_dat(
       ma_loai_phong=room_id,
       checkin=checkin_date,
       checkout=checkout_date
   )


   so_con_lai = room.SoLuongPhong - so_da_dat


   if so_con_lai < so_phong:
       return False, "Loại phòng này không còn đủ phòng trống."


   tong_tien = Decimal(str(room.GiaMoiDem)) * so_dem * so_phong


   booking = DatPhong(
       MaDatPhongCode=generate_booking_code(),
       MaNguoiDung=user_id,
       MaKhachSan=hotel_id,
       NgayNhanPhong=checkin_date,
       NgayTraPhong=checkout_date,
       SoNguoiLuuTru=so_nguoi_luu_tru,
       TongTien=tong_tien,
       TrangThaiDatPhong=0
   )


   db.session.add(booking)
   db.session.flush()


   detail = ChiTietDatPhong(
       MaDatPhong=booking.MaDatPhong,
       MaLoaiPhong=room_id,
       SoLuongPhongDat=so_phong,
       DonGiaMoiDem=room.GiaMoiDem,
       SoDem=so_dem,
       ThanhTien=tong_tien
   )


   db.session.add(detail)
   db.session.commit()


   print("ĐÃ TẠO ĐƠN:", booking.MaDatPhong, booking.MaDatPhongCode)


   return True, booking.MaDatPhong

def get_pending_booking_page_data(booking_id, user_id):
   booking = DatPhong.query.get(booking_id)


   if not booking:
       print("KHÔNG TÌM THẤY BOOKING:", booking_id)
       return None


   print("BOOKING ID:", booking.MaDatPhong)
   print("BOOKING USER:", booking.MaNguoiDung)
   print("SESSION USER:", user_id)


   if int(booking.MaNguoiDung) != int(user_id):
       print("SAI USER")
       return None


   detail = ChiTietDatPhong.query.filter_by(
       MaDatPhong=booking.MaDatPhong
   ).first()


   if not detail:
       print("KHÔNG TÌM THẤY CHI TIẾT ĐẶT PHÒNG")
       return None


   room = LoaiPhong.query.get(detail.MaLoaiPhong)
   hotel = KhachSan.query.get(booking.MaKhachSan)


   if not room:
       print("KHÔNG TÌM THẤY LOẠI PHÒNG")
       return None


   if not hotel:
       print("KHÔNG TÌM THẤY KHÁCH SẠN")
       return None


   return {
       "booking": booking,
       "detail": detail,
       "room": room,
       "hotel": hotel,
       "hotel_images": get_hotel_images(hotel),
       "room_images": get_room_images(room),
       "checkin": booking.NgayNhanPhong,
       "checkout": booking.NgayTraPhong,
       "so_dem": detail.SoDem,
       "so_phong": detail.SoLuongPhongDat,
       "so_nguoi_lon": booking.SoNguoiLuuTru,
       "tong_tien_phong": booking.TongTien,
       "phi_dich_vu": Decimal(str(booking.TongTien)) * Decimal("0.10")
   }
def delete_expired_pending_booking(booking_id, user_id):
   booking = DatPhong.query.get(booking_id)


   if not booking:
       return False, "Không tìm thấy đơn."


   if booking.MaNguoiDung != user_id:
       return False, "Bạn không có quyền xóa đơn này."


   if booking.TrangThaiDatPhong != 0:
       return False, "Đơn này không còn ở trạng thái chờ thanh toán."


   try:
       ChiTietDatPhong.query.filter_by(MaDatPhong=booking_id).delete()
       db.session.delete(booking)
       db.session.commit()
       return True, "Đã xóa đơn giữ phòng hết hạn."
   except Exception as e:
       db.session.rollback()
       return False, str(e)

def cleanup_expired_pending_bookings():
   limit_time = datetime.utcnow() - timedelta(minutes=8)


   expired_bookings = DatPhong.query.filter(
       DatPhong.TrangThaiDatPhong == 0,
       DatPhong.NgayTao < limit_time
   ).all()


   for booking in expired_bookings:
       ChiTietDatPhong.query.filter_by(MaDatPhong=booking.MaDatPhong).delete()
       db.session.delete(booking)


   if expired_bookings:
       db.session.commit()


"""TRANG QUẢNG LÝ LOẠI PHÒNG"""
def get_room_types_management_by_hotel(ma_khach_san, tab="loai-phong"):
    hotel = get_hotel_by_id(ma_khach_san)

    if not hotel:
        return None

    room_types = LoaiPhong.query.filter_by(MaKhachSan=ma_khach_san).all()

    for room in room_types:
        room.first_image = get_first_room_image(room.ThuMucAnh)

    tong_so_loai_phong = len(room_types)
    tong_so_phong = sum(room.SoLuongPhong for room in room_types)

    today = date.today()
    tomorrow = today + timedelta(days=1)

    so_phong_dang_co_nguoi_o = 0
    phong_dang_o = []
    phong_trong = []

    for room in room_types:
        chi_tiet_co_hieu_luc = ChiTietDatPhong.query.join(DatPhong).filter(
            ChiTietDatPhong.MaLoaiPhong == room.MaLoaiPhong,
            DatPhong.MaKhachSan == ma_khach_san,
            DatPhong.TrangThaiDatPhong.in_([0, 1])
        ).all()

        chi_tiet_dang_o = []

        for item in chi_tiet_co_hieu_luc:
            if is_booking_currently_occupying_room(item.dat_phong):
                chi_tiet_dang_o.append(item)

        so_dang_o = sum(item.SoLuongPhongDat for item in chi_tiet_dang_o)

        room.so_dang_o = so_dang_o

        so_trong = max(0, room.SoLuongPhong - so_dang_o)

        if so_dang_o > 0:
            phong_dang_o.append({
                "room": room,
                "so_luong": so_dang_o,
                "orders": chi_tiet_dang_o
            })

        if so_trong > 0:
            phong_trong.append({
                "room": room,
                "so_luong": so_trong
            })

        so_phong_dang_co_nguoi_o += so_dang_o

    so_phong_trong = max(0, tong_so_phong - so_phong_dang_co_nguoi_o)

    don_dat_phong = DatPhong.query.filter_by(
        MaKhachSan=ma_khach_san
    ).order_by(DatPhong.NgayTao.desc()).all()

    don_da_huy = DatPhong.query.filter_by(
        MaKhachSan=ma_khach_san,
        TrangThaiDatPhong=2
    ).order_by(DatPhong.NgayTao.desc()).all()

    for booking in don_dat_phong:
        room_names = []

        for item in booking.chi_tiet_dat_phongs:
            if item.loai_phong:
                room_names.append(item.loai_phong.TenLoaiPhong)

        booking.ten_loai_phong = ", ".join(room_names)

    for booking in don_da_huy:
        room_names = []

        for item in booking.chi_tiet_dat_phongs:
            if item.loai_phong:
                room_names.append(item.loai_phong.TenLoaiPhong)

        booking.ten_loai_phong = ", ".join(room_names)

    tong_so_don_dat_phong = len(don_dat_phong)
    so_don_da_huy = len(don_da_huy)

    # Doanh thu thực tế: chỉ tính đơn đã hoàn thành
    doanh_thu_hoan_thanh = db.session.query(
        func.coalesce(func.sum(DatPhong.TongTien), 0)
    ).filter(
        DatPhong.MaKhachSan == ma_khach_san,
        DatPhong.TrangThaiDatPhong == 3
    ).scalar()

    phi_he_thong_hoan_thanh = doanh_thu_hoan_thanh * Decimal("0.10")
    thu_nhap_thuc_nhan = doanh_thu_hoan_thanh - phi_he_thong_hoan_thanh

    # Doanh thu ước tính: tính cả đơn đã thanh toán + hoàn thành
    doanh_thu_uoc_tinh = db.session.query(
        func.coalesce(func.sum(DatPhong.TongTien), 0)
    ).filter(
        DatPhong.MaKhachSan == ma_khach_san,
        DatPhong.TrangThaiDatPhong.in_([1, 3])
    ).scalar()

    phi_he_thong_uoc_tinh = doanh_thu_uoc_tinh * Decimal("0.10")
    thu_nhap_uoc_tinh = doanh_thu_uoc_tinh - phi_he_thong_uoc_tinh

    for booking in don_dat_phong:
        booking.trang_thai_text = hien_thi_trang_thai_dat_phong(booking.TrangThaiDatPhong)

    for booking in don_da_huy:
        booking.trang_thai_text = hien_thi_trang_thai_dat_phong(booking.TrangThaiDatPhong)

    return {
        "hotel": hotel,
        "room_types": room_types,

        "tong_so_loai_phong": tong_so_loai_phong,
        "tong_so_phong": tong_so_phong,
        "so_phong_dang_co_nguoi_o": so_phong_dang_co_nguoi_o,
        "so_phong_trong": so_phong_trong,

        "tong_so_don_dat_phong": tong_so_don_dat_phong,
        "so_don_da_huy": so_don_da_huy,
        "tong_thu_nhap": doanh_thu_uoc_tinh,

        "doanh_thu_hoan_thanh": doanh_thu_hoan_thanh,
        "phi_he_thong_hoan_thanh": phi_he_thong_hoan_thanh,
        "thu_nhap_thuc_nhan": thu_nhap_thuc_nhan,

        "doanh_thu_uoc_tinh": doanh_thu_uoc_tinh,
        "phi_he_thong_uoc_tinh": phi_he_thong_uoc_tinh,
        "thu_nhap_uoc_tinh": thu_nhap_uoc_tinh,
        "payouts": get_payouts_by_hotel(ma_khach_san),

        "phong_dang_o": phong_dang_o,
        "phong_trong": phong_trong,
        "don_dat_phong": don_dat_phong,
        "don_da_huy": don_da_huy,
        "tab": tab
    }

def get_first_room_image(folder):
    """
    folder trong DB ví dụ: loaiphong/lp_1
    trả về cho HTML: images/loaiphong/lp_1/1.png
    """
    if not folder:
        return None

    # Đường dẫn thật trong máy
    base_path = os.path.join(current_app.root_path, "static", "images", folder)

    print("DEBUG folder:", folder)
    print("DEBUG base_path:", base_path)
    print("DEBUG exists:", os.path.exists(base_path))

    if not os.path.exists(base_path):
        return None

    files = sorted(os.listdir(base_path))

    for file_name in files:
        if file_name.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            return f"images/{folder}/{file_name}"

    return None

"""Dùng cho trang quản LÝ, chỉnh sửa loại phòng"""
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def get_room_image_list(folder):
    """
    folder ví dụ: loaiphong/lp_1
    trả về list:
    [
        {'filename': '1.png', 'url': 'images/loaiphong/lp_1/1.png'}
    ]
    """
    if not folder:
        return []

    folder_path = os.path.join(current_app.root_path, "static", "images", folder)

    if not os.path.exists(folder_path):
        return []

    images = []

    for file_name in sorted(os.listdir(folder_path)):
        ext = os.path.splitext(file_name)[1].lower()

        if ext in ALLOWED_IMAGE_EXTENSIONS:
            images.append({
                "filename": file_name,
                "url": f"images/{folder}/{file_name}"
            })

    return images



def delete_room_image(folder, filename):
    if not folder or not filename:
        return False, "Thiếu thông tin ảnh"

    folder_path = os.path.join(current_app.root_path, "static", "images", folder)
    file_path = os.path.join(folder_path, filename)

    if os.path.exists(file_path):
        os.remove(file_path)
        return True, "Xóa ảnh thành công"

    return False, "Không tìm thấy ảnh"

def get_room_edit_data(hotel_id, room_id):
    hotel = get_hotel_by_id(hotel_id)
    room = get_room_type_by_id(room_id)

    if not hotel or not room:
        return None

    if room.MaKhachSan != hotel.MaKhachSan:
        return None

    room_images = get_room_image_list(room.ThuMucAnh)

    return {
        "hotel": hotel,
        "room": room,
        "room_images": room_images,
        "all_amenities": get_room_amenities_without_db_change(),
        "room_amenity_ids": [amenity.MaTienIch for amenity in room.tien_ichs]
    }


def update_room_basic_info(room_id, ten_loai_phong, mo_ta, gia_moi_dem,
                           so_nguoi_toi_da, so_luong_phong, trang_thai_hoat_dong):
    room = get_room_type_by_id(room_id)

    if not room:
        return False, "Không tìm thấy loại phòng"

    room.TenLoaiPhong = ten_loai_phong
    room.MoTa = mo_ta
    room.GiaMoiDem = gia_moi_dem
    room.SoNguoiToiDa = so_nguoi_toi_da
    room.SoLuongPhong = so_luong_phong
    room.TrangThaiHoatDong = trang_thai_hoat_dong
    room.NgayCapNhat = datetime.now()

    try:
        db.session.commit()
        return True, room
    except Exception as e:
        db.session.rollback()
        return False, str(e)


def update_room_amenities(room_id, amenity_ids):
    room = get_room_type_by_id(room_id)

    if not room:
        return False, "Không tìm thấy loại phòng"

    try:
        room.tien_ichs.clear()

        for amenity_id in amenity_ids:
            amenity = TienIch.query.get(int(amenity_id))
            if amenity:
                room.tien_ichs.append(amenity)

        db.session.commit()
        return True, room
    except Exception as e:
        db.session.rollback()
        return False, str(e)


def update_room_status(ma_loai_phong, trang_thai):
    room = get_room_type_by_id(ma_loai_phong)

    if not room:
        return False, "Không tìm thấy loại phòng"

    room.TrangThaiHoatDong = trang_thai
    room.NgayCapNhat = datetime.now()

    try:
        db.session.commit()
        return True, room
    except Exception as e:
        db.session.rollback()
        return False, str(e)

def get_room_amenities_without_db_change():
    """
    Lọc tiện ích phù hợp với loại phòng mà không cần sửa database.
    Dựa vào tên tiện ích.
    """
    room_amenity_names = [
        "Wifi miễn phí",
        "Điều hòa",
        "Máy sấy tóc",
        "Ban công",
        "Bồn tắm",
        "TV",
        "Mini bar",
        "Bao gồm bữa sáng",
        "Tủ lạnh",
        "Ấm đun nước",
        "Bàn làm việc",
        "Máy pha cà phê"
    ]

    return TienIch.query.filter(
        TienIch.TenTienIch.in_(room_amenity_names)
    ).order_by(TienIch.TenTienIch.asc()).all()

def get_next_image_index(folder_path):
    """
    Tìm số lớn nhất trong thư mục ảnh rồi trả về số tiếp theo.
    Ví dụ đang có 1.png, 2.png, 5.png -> trả về 6
    """
    max_index = 0

    if not os.path.exists(folder_path):
        return 1

    for file_name in os.listdir(folder_path):
        name, ext = os.path.splitext(file_name)

        if ext.lower() in ALLOWED_IMAGE_EXTENSIONS and name.isdigit():
            max_index = max(max_index, int(name))

    return max_index + 1


def save_room_images(folder, files):
    """
    folder trong DB ví dụ: loaiphong/lp_1

    Lưu ảnh vào:
    app/static/images/loaiphong/lp_1/

    Nếu đã có:
    1.png, 2.png, 5.png

    Ảnh mới sẽ lưu thành:
    6.png, 7.png, ...
    """
    if not folder:
        return False, "Loại phòng chưa có thư mục ảnh"

    folder_path = os.path.join(
        current_app.root_path,
        "static",
        "images",
        folder
    )

    os.makedirs(folder_path, exist_ok=True)

    next_index = get_next_image_index(folder_path)
    saved_count = 0

    for file in files:
        if not file or file.filename == "":
            continue

        original_filename = secure_filename(file.filename)
        _, ext = os.path.splitext(original_filename)
        ext = ext.lower()

        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            continue

        new_filename = f"{next_index}{ext}"
        save_path = os.path.join(folder_path, new_filename)

        file.save(save_path)

        next_index += 1
        saved_count += 1

    if saved_count == 0:
        return False, "Không có ảnh hợp lệ để lưu"

    return True, f"Đã thêm {saved_count} ảnh"


# ===== Hàm xme chi ntieest đơn trong qly loaiphong
def get_booking_detail_for_owner(booking_id):
    booking = DatPhong.query.get(booking_id)

    if not booking:
        return None

    booking.trang_thai_text = hien_thi_trang_thai_dat_phong(booking.TrangThaiDatPhong)

    payment = ThanhToan.query.filter_by(MaDatPhong=booking_id).first()

    return {
        "booking": booking,
        "hotel": booking.khach_san,
        "customer": booking.nguoi_dung,
        "details": booking.chi_tiet_dat_phongs,
        "payment": payment
    }
#
def is_room_type_currently_occupied(room_id):
    today = date.today()
    tomorrow = today + timedelta(days=1)

    count = ChiTietDatPhong.query.join(DatPhong).filter(
        ChiTietDatPhong.MaLoaiPhong == room_id,
        DatPhong.TrangThaiDatPhong.in_([0, 1]),
        DatPhong.NgayNhanPhong < tomorrow,
        DatPhong.NgayTraPhong > today
    ).count()

    return count > 0

def delete_room_type(room_id):
    room = get_room_type_by_id(room_id)

    if not room:
        return False, "Không tìm thấy loại phòng."

    try:
        db.session.delete(room)
        db.session.commit()
        return True, "Xóa loại phòng thành công."
    except Exception as e:
        db.session.rollback()
        return False, str(e)

def cancel_booking_by_owner(booking_id):
    booking = DatPhong.query.get(booking_id)

    if not booking:
        return False, "Không tìm thấy đơn đặt phòng.", None

    hotel_id = booking.MaKhachSan
    now = datetime.now()

    checkin_datetime = datetime.combine(
        booking.NgayNhanPhong,
        time(14, 0)
    )

    checkout_datetime = datetime.combine(
        booking.NgayTraPhong,
        time(12, 0)
    )

    # Nếu đang trong thời gian lưu trú thì không cho hủy
    if checkin_datetime <= now < checkout_datetime:
        return False, "Không thể hủy đơn vì khách đang trong thời gian lưu trú.", hotel_id



    try:
        booking.TrangThaiDatPhong = 2  # Đã hủy
        if hasattr(booking, "NgayCapNhat"):
            booking.NgayCapNhat = datetime.now()

        payment = ThanhToan.query.filter_by(MaDatPhong=booking_id).first()

        if payment:
            if payment.TrangThaiThanhToan == 1:
                payment.TrangThaiThanhToan = 3  # Đã hoàn tiền
            else:
                payment.TrangThaiThanhToan = 2  # Thất bại / hủy thanh toán

        db.session.commit()
        return True, "Hủy đơn đặt phòng thành công.", hotel_id

    except Exception as e:
        db.session.rollback()
        return False, str(e), hotel_id

def create_room_type(ma_khach_san, ten_loai_phong, mo_ta, gia_moi_dem,
                     so_nguoi_toi_da, so_luong_phong, trang_thai_hoat_dong,
                     amenity_ids):
    try:
        room = LoaiPhong(
            MaKhachSan=ma_khach_san,
            TenLoaiPhong=ten_loai_phong,
            MoTa=mo_ta,
            GiaMoiDem=gia_moi_dem,
            SoNguoiToiDa=so_nguoi_toi_da,
            SoLuongPhong=so_luong_phong,
            TrangThaiHoatDong=trang_thai_hoat_dong
        )

        db.session.add(room)
        db.session.flush()

        room.ThuMucAnh = f"loaiphong/lp_{room.MaLoaiPhong}"

        folder_path = os.path.join(
            current_app.root_path,
            "static",
            "images",
            room.ThuMucAnh
        )
        os.makedirs(folder_path, exist_ok=True)

        for amenity_id in amenity_ids:
            amenity = TienIch.query.get(int(amenity_id))
            if amenity:
                room.tien_ichs.append(amenity)

        db.session.commit()
        return True, room

    except Exception as e:
        db.session.rollback()
        return False, str(e)


def room_type_has_any_booking(room_id):
    return ChiTietDatPhong.query.filter_by(MaLoaiPhong=room_id).count() > 0


def room_type_has_active_or_future_booking(room_id):
    today = date.today()

    count = ChiTietDatPhong.query.join(DatPhong).filter(
        ChiTietDatPhong.MaLoaiPhong == room_id,

        # chỉ tính đơn còn hiệu lực
        DatPhong.TrangThaiDatPhong.in_([0, 1]),

        # đơn đang ở hoặc đơn sắp tới
        DatPhong.NgayTraPhong > today
    ).count()

    return count > 0

def auto_complete_expired_bookings():
    now = datetime.now()

    bookings = DatPhong.query.filter(
        DatPhong.TrangThaiDatPhong.in_([0, 1])
    ).all()

    updated = False

    for booking in bookings:
        checkout_datetime = datetime.combine(
            booking.NgayTraPhong,
            time(12, 0)
        )

        if now >= checkout_datetime:
            booking.TrangThaiDatPhong = 3
            create_payout_for_completed_booking(booking)
            updated = True

    if updated:
        db.session.commit()

def is_booking_currently_occupying_room(booking):
    now = datetime.now()

    checkin_datetime = datetime.combine(
        booking.NgayNhanPhong,
        time(14, 0)
    )

    checkout_datetime = datetime.combine(
        booking.NgayTraPhong,
        time(12, 0)
    )

    return checkin_datetime <= now < checkout_datetime

def get_payouts_by_hotel(ma_khach_san):
    payouts = ChuyenTienKhachSan.query.filter_by(
        MaKhachSan=ma_khach_san
    ).order_by(
        ChuyenTienKhachSan.ThoiGianChuyenTien.desc()
    ).all()

    return payouts
def create_payout_for_completed_booking(booking):
    existing = ChuyenTienKhachSan.query.filter_by(
        MaDatPhong=booking.MaDatPhong
    ).first()

    if existing:
        return

    phi_he_thong = Decimal(str(booking.TongTien)) * Decimal("0.10")
    so_tien_chuyen = Decimal(str(booking.TongTien)) - phi_he_thong

    payout = ChuyenTienKhachSan(
        MaDatPhong=booking.MaDatPhong,
        MaKhachSan=booking.MaKhachSan,
        TongTienDonHang=booking.TongTien,
        PhiHeThong=phi_he_thong,
        SoTienChuyenChoKhachSan=so_tien_chuyen,

        # 0 = chờ chuyển tiền, 1 = đã chuyển, 2 = thất bại
        TrangThaiChuyenTien=0,
        ThoiGianChuyenTien=None
    )

    db.session.add(payout)

#===== đơn hoàn thành mà chưa có payout thì sẽ bị thiu, nên là TA thêm cho nó bất kỳ đơn nào đã hoàn thành cũng sẽ load tạo đơn chuyển tiền ks*nếu chưa có, tứuc auto check á
def ensure_payouts_for_completed_bookings():
    completed_bookings = DatPhong.query.filter_by(
        TrangThaiDatPhong=3  # Hoàn thành
    ).all()

    created = False

    for booking in completed_bookings:
        existing = ChuyenTienKhachSan.query.filter_by(
            MaDatPhong=booking.MaDatPhong
        ).first()

        if not existing:
            phi = Decimal(str(booking.TongTien)) * Decimal("0.10")
            net = Decimal(str(booking.TongTien)) - phi

            payout = ChuyenTienKhachSan(
                MaDatPhong=booking.MaDatPhong,
                MaKhachSan=booking.MaKhachSan,
                TongTienDonHang=booking.TongTien,
                PhiHeThong=phi,
                SoTienChuyenChoKhachSan=net,
                TrangThaiChuyenTien=0,
                ThoiGianChuyenTien=None
            )

            db.session.add(payout)
            created = True

    if created:
        db.session.commit()

def get_completed_bookings_can_review(hotel_id, user_id):
    """
    lấy các đơn hoàn thành của ngdung tại ks này mà chưa từng được đánh giá.
    """
    completed_bookings = DatPhong.query.filter_by(
        MaKhachSan=hotel_id,
        MaNguoiDung=user_id,
        TrangThaiDatPhong=3
    ).all()

    result = []

    for booking in completed_bookings:
        existed_review = DanhGia.query.filter_by(
            MaDatPhong=booking.MaDatPhong
        ).first()

        if existed_review:
            continue

        for detail in booking.chi_tiet_dat_phongs:
            result.append({
                "booking": booking,
                "detail": detail,
                "room": detail.loai_phong
            })

    return result


def create_review(ma_dat_phong, ma_nguoi_dung, ma_khach_san, so_sao, binh_luan):
    booking = DatPhong.query.get(ma_dat_phong)

    if not booking:
        return False, "Không tìm thấy đơn đặt phòng."

    if booking.MaNguoiDung != ma_nguoi_dung:
        return False, "Bạn không có quyền đánh giá đơn này."

    if booking.MaKhachSan != ma_khach_san:
        return False, "Đơn đặt phòng không thuộc khách sạn này."

    if booking.TrangThaiDatPhong != 3:
        return False, "Bạn chỉ được đánh giá sau khi đơn hoàn thành."

    existed_review = DanhGia.query.filter_by(MaDatPhong=ma_dat_phong).first()
    if existed_review:
        return False, "Bạn đã đánh giá đơn đặt phòng này rồi."

    review = DanhGia(
        MaDatPhong=ma_dat_phong,
        MaNguoiDung=ma_nguoi_dung,
        MaKhachSan=ma_khach_san,
        SoSao=int(so_sao),
        BinhLuan=binh_luan
    )

    db.session.add(review)

    reviews = DanhGia.query.filter_by(MaKhachSan=ma_khach_san).all()
    total = sum(r.SoSao for r in reviews) + int(so_sao)
    count = len(reviews) + 1

    hotel = KhachSan.query.get(ma_khach_san)
    if hotel:
        hotel.DiemDanhGiaTrungBinh = round(total / count, 2)

    db.session.commit()
    return True, "Đánh giá khách sạn thành công."
