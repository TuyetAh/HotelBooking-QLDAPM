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

    return render_template(
        "index.html"
    )


# =========================================================
# CHI TIẾT KHÁCH SẠN
# =========================================================
@app.route("/khach-san/<int:hotel_id>")
def chi_tiet_khach_san(hotel_id):

    return render_template("ChiTietKhachSan.html")



if __name__ == "__main__":
    app.run(debug=True)