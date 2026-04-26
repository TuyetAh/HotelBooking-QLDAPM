from flask import render_template, request, redirect, url_for, session, flash
from functools import wraps
from app import create_app
from app.dao import (
    check_login,
    register_user,
    get_all_hotels,
    search_hotels,
    get_hotel_by_id,
    get_hotel_detail_data,
    get_bookings_by_user,
    get_user_by_id,
    build_hotel_card_data,
    update_user,
    doi_mat_khau,
    create_hotel_owner_account,
    get_all_tien_ich_khach_san,
    create_hotel_full,
    get_hotels_by_owner,
    get_featured_hotels,
    search_hotels_advanced,
    get_all_amenities
)

app = create_app()
app.secret_key = "hotel_booking_secret_key"

# =========================================================
# TRANG CHỦ
# =========================================================
@app.route("/")
def index():
    featured_hotels = get_featured_hotels()
    hotel_cards = [build_hotel_card_data(hotel) for hotel in featured_hotels]
    return render_template("index.html", hotel_cards=hotel_cards)


# =========================================================
# ĐĂNG KÝ
# =========================================================
@app.route("/dang-ky", methods=["GET", "POST"])
def dang_ky():
    return render_template("DangKy.html")


# =========================================================
# ĐĂNG NHẬP
# =========================================================
@app.route("/dang-nhap", methods=["GET", "POST"])
def dang_nhap():

    return render_template("DangNhap.html")
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

    return render_template(
        "TimKiemKhachSan.html",
        hotel_cards=hotel_cards,
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
        selected_tien_ich=tien_ich_ids,
        total_results=len(hotel_cards)
    )


# =========================================================
# CHI TIẾT KHÁCH SẠN
# =========================================================
@app.route("/khach-san/<int:hotel_id>")
def chi_tiet_khach_san(hotel_id):

    return render_template("ChiTietKhachSan.html")



if __name__ == "__main__":
    app.run(debug=True)