from datetime import datetime
from app import db


# =========================================================
# BẢNG NGƯỜI DÙNG
# VaiTro:
# 0 = Admin
# 1 = Chủ khách sạn
# 2 = Khách hàng
#
# TrangThaiHoatDong:
# 0 = Dừng hoạt động
# 1 = Đang hoạt động
# =========================================================
class NguoiDung(db.Model):
    __tablename__ = "NguoiDung"

    MaNguoiDung = db.Column(db.Integer, primary_key=True, autoincrement=True)
    TenDangNhap = db.Column(db.String(50), unique=True, nullable=False)
    MatKhau = db.Column(db.String(255), nullable=False)
    HoTen = db.Column(db.String(100), nullable=False)
    SoDienThoai = db.Column(db.String(20), nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    SoTaiKhoanNganHang = db.Column(db.String(50), nullable=True)
    VaiTro = db.Column(db.Integer, nullable=False)
    TrangThaiHoatDong = db.Column(db.Integer, nullable=False, default=1)
    NgayTao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    NgayCapNhat = db.Column(db.DateTime, nullable=True)

    # 1 người dùng có thể là 1 chủ khách sạn
    chu_khach_san = db.relationship(
        "ChuKhachSan",
        back_populates="nguoi_dung",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # 1 người dùng có nhiều đơn đặt phòng
    dat_phongs = db.relationship(
        "DatPhong",
        back_populates="nguoi_dung",
        lazy=True
    )

    # 1 người dùng có thể có nhiều đánh giá
    danh_gias = db.relationship(
        "DanhGia",
        back_populates="nguoi_dung",
        lazy=True
    )

    def __repr__(self):
        return f"<NguoiDung {self.TenDangNhap}>"



# =========================================================
# BẢNG CHỦ KHÁCH SẠN
# =========================================================
class ChuKhachSan(db.Model):
    __tablename__ = "ChuKhachSan"

    MaChuKhachSan = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MaNguoiDung = db.Column(
        db.Integer,
        db.ForeignKey("NguoiDung.MaNguoiDung", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        unique=True
    )
    TenDoanhNghiep = db.Column(db.String(200), nullable=True)
    DiaChiDoanhNghiep = db.Column(db.String(255), nullable=True)

    nguoi_dung = db.relationship(
        "NguoiDung",
        back_populates="chu_khach_san"
    )

    khach_sans = db.relationship(
        "KhachSan",
        back_populates="chu_khach_san",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ChuKhachSan {self.MaChuKhachSan}>"



# =========================================================
# BẢNG KHÁCH SẠN
#
# ChinhSachHuy:
# 0 = Trước 1 ngày
# 1 = Trước 3 ngày
# 2 = Không cho hủy
#
# TrangThaiDuyet:
# 0 = Chờ duyệt
# 1 = Đã duyệt
# 2 = Từ chối
#
# TrangThaiHoatDong:
# 0 = Dừng hoạt động
# 1 = Đang hoạt động
# =========================================================
class KhachSan(db.Model):
    __tablename__ = "KhachSan"

    MaKhachSan = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MaChuKhachSan = db.Column(
        db.Integer,
        db.ForeignKey("ChuKhachSan.MaChuKhachSan", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )
    TenKhachSan = db.Column(db.String(200), nullable=False)
    ThanhPho = db.Column(db.String(100), nullable=False)
    DiaChi = db.Column(db.String(255), nullable=False)
    ViTriNoiBat = db.Column(db.String(255), nullable=True)
    SoDienThoaiLienHe = db.Column(db.String(20), nullable=False)
    MoTa = db.Column(db.Text, nullable=True)
    QuyDinhKhachSan = db.Column(db.Text, nullable=True)
    ChinhSachHuy = db.Column(db.Integer, nullable=False)
    ThuMucAnh = db.Column(db.String(255), nullable=True)
    TrangThaiDuyet = db.Column(db.Integer, nullable=False, default=0)
    LyDoTuChoi = db.Column(db.String(255), nullable=True)
    DiemDanhGiaTrungBinh = db.Column(db.Numeric(3, 2), nullable=False, default=0)
    TrangThaiHoatDong = db.Column(db.Integer, nullable=False, default=1)
    NgayTao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    NgayCapNhat = db.Column(db.DateTime, nullable=True)
    NgayDuyet = db.Column(db.DateTime, nullable=True)

    chu_khach_san = db.relationship(
        "ChuKhachSan",
        back_populates="khach_sans"
    )

    # 1 khách sạn có nhiều loại phòng
    loai_phongs = db.relationship(
        "LoaiPhong",
        back_populates="khach_san",
        lazy=True,
        cascade="all, delete-orphan"
    )

    # 1 khách sạn có nhiều đơn đặt phòng
    dat_phongs = db.relationship(
        "DatPhong",
        back_populates="khach_san",
        lazy=True
    )

    # 1 khách sạn có nhiều đánh giá
    danh_gias = db.relationship(
        "DanhGia",
        back_populates="khach_san",
        lazy=True
    )

    # 1 khách sạn có thể có nhiều bản ghi chuyển tiền qua các đơn
    chuyen_tien_khach_sans = db.relationship(
        "ChuyenTienKhachSan",
        back_populates="khach_san",
        lazy=True
    )

    # nhiều-nhiều với tiện ích
    tien_ichs = db.relationship(
        "TienIch",
        secondary="TienIchKhachSan",
        back_populates="khach_sans",
        lazy=True
    )

    def __repr__(self):
        return f"<KhachSan {self.TenKhachSan}>"



# =========================================================
# BẢNG TIỆN ÍCH
# =========================================================
class TienIch(db.Model):
    __tablename__ = "TienIch"

    MaTienIch = db.Column(db.Integer, primary_key=True, autoincrement=True)
    TenTienIch = db.Column(db.String(100), unique=True, nullable=False)

    khach_sans = db.relationship(
        "KhachSan",
        secondary="TienIchKhachSan",
        back_populates="tien_ichs",
        lazy=True
    )

    loai_phongs = db.relationship(
        "LoaiPhong",
        secondary="TienIchLoaiPhong",
        back_populates="tien_ichs",
        lazy=True
    )

    def __repr__(self):
        return f"<TienIch {self.TenTienIch}>"



# =========================================================
# BẢNG PHỤ TIỆN ÍCH KHÁCH SẠN
# =========================================================
class TienIchKhachSan(db.Model):
    __tablename__ = "TienIchKhachSan"

    MaKhachSan = db.Column(
        db.Integer,
        db.ForeignKey("KhachSan.MaKhachSan", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True
    )
    MaTienIch = db.Column(
        db.Integer,
        db.ForeignKey("TienIch.MaTienIch", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True
    )



# =========================================================
# BẢNG LOẠI PHÒNG
#
# TrangThaiHoatDong:
# 0 = Dừng hoạt động
# 1 = Đang hoạt động
# =========================================================
class LoaiPhong(db.Model):
    __tablename__ = "LoaiPhong"

    MaLoaiPhong = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MaKhachSan = db.Column(
        db.Integer,
        db.ForeignKey("KhachSan.MaKhachSan", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )
    TenLoaiPhong = db.Column(db.String(100), nullable=False)
    MoTa = db.Column(db.Text, nullable=True)
    GiaMoiDem = db.Column(db.Numeric(18, 2), nullable=False)
    SoNguoiToiDa = db.Column(db.Integer, nullable=False)
    SoLuongPhong = db.Column(db.Integer, nullable=False)
    ThuMucAnh = db.Column(db.String(255), nullable=True)
    TrangThaiHoatDong = db.Column(db.Integer, nullable=False, default=1)
    NgayTao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    NgayCapNhat = db.Column(db.DateTime, nullable=True)

    khach_san = db.relationship(
        "KhachSan",
        back_populates="loai_phongs"
    )

    chi_tiet_dat_phongs = db.relationship(
        "ChiTietDatPhong",
        back_populates="loai_phong",
        lazy=True
    )

    tien_ichs = db.relationship(
        "TienIch",
        secondary="TienIchLoaiPhong",
        back_populates="loai_phongs",
        lazy=True
    )

    def __repr__(self):
        return f"<LoaiPhong {self.TenLoaiPhong}>"



# =========================================================
# BẢNG PHỤ TIỆN ÍCH LOẠI PHÒNG
# =========================================================
class TienIchLoaiPhong(db.Model):
    __tablename__ = "TienIchLoaiPhong"

    MaLoaiPhong = db.Column(
        db.Integer,
        db.ForeignKey("LoaiPhong.MaLoaiPhong", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True
    )
    MaTienIch = db.Column(
        db.Integer,
        db.ForeignKey("TienIch.MaTienIch", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True
    )



# =========================================================
# BẢNG ĐẶT PHÒNG
#
# TrangThaiDatPhong:
# 0 = Chờ thanh toán
# 1 = Đã thanh toán
# 2 = Đã hủy
# 3 = Hoàn thành
# =========================================================
class DatPhong(db.Model):
    __tablename__ = "DatPhong"

    MaDatPhong = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MaDatPhongCode = db.Column(db.String(50), unique=True, nullable=False)
    MaNguoiDung = db.Column(
        db.Integer,
        db.ForeignKey("NguoiDung.MaNguoiDung", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False
    )
    MaKhachSan = db.Column(
        db.Integer,
        db.ForeignKey("KhachSan.MaKhachSan", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False
    )
    NgayNhanPhong = db.Column(db.Date, nullable=False)
    NgayTraPhong = db.Column(db.Date, nullable=False)
    SoNguoiLuuTru = db.Column(db.Integer, nullable=False)
    TongTien = db.Column(db.Numeric(18, 2), nullable=False)
    TrangThaiDatPhong = db.Column(db.Integer, nullable=False, default=0)
    NgayTao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    nguoi_dung = db.relationship(
        "NguoiDung",
        back_populates="dat_phongs"
    )

    khach_san = db.relationship(
        "KhachSan",
        back_populates="dat_phongs"
    )

    chi_tiet_dat_phongs = db.relationship(
        "ChiTietDatPhong",
        back_populates="dat_phong",
        lazy=True,
        cascade="all, delete-orphan"
    )

    # 1 đơn có tối đa 1 thanh toán
    thanh_toan = db.relationship(
        "ThanhToan",
        back_populates="dat_phong",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # 1 đơn có tối đa 1 hoàn tiền
    hoan_tien = db.relationship(
        "HoanTien",
        back_populates="dat_phong",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # 1 đơn có tối đa 1 đánh giá
    danh_gia = db.relationship(
        "DanhGia",
        back_populates="dat_phong",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # 1 đơn có tối đa 1 bản ghi chuyển tiền
    chuyen_tien_khach_san = db.relationship(
        "ChuyenTienKhachSan",
        back_populates="dat_phong",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<DatPhong {self.MaDatPhongCode}>"



# =========================================================
# BẢNG CHI TIẾT ĐẶT PHÒNG
# =========================================================
class ChiTietDatPhong(db.Model):
    __tablename__ = "ChiTietDatPhong"

    MaChiTietDatPhong = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MaDatPhong = db.Column(
        db.Integer,
        db.ForeignKey("DatPhong.MaDatPhong", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )
    MaLoaiPhong = db.Column(
        db.Integer,
        db.ForeignKey("LoaiPhong.MaLoaiPhong", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False
    )
    SoLuongPhongDat = db.Column(db.Integer, nullable=False)
    DonGiaMoiDem = db.Column(db.Numeric(18, 2), nullable=False)
    SoDem = db.Column(db.Integer, nullable=False)
    ThanhTien = db.Column(db.Numeric(18, 2), nullable=False)

    dat_phong = db.relationship(
        "DatPhong",
        back_populates="chi_tiet_dat_phongs"
    )

    loai_phong = db.relationship(
        "LoaiPhong",
        back_populates="chi_tiet_dat_phongs"
    )

    def __repr__(self):
        return f"<ChiTietDatPhong {self.MaChiTietDatPhong}>"



# =========================================================
# BẢNG THANH TOÁN
#
# TrangThaiThanhToan:
# 0 = Chờ thanh toán
# 1 = Thành công
# 2 = Thất bại
# 3 = Đã hoàn tiền
# =========================================================
class ThanhToan(db.Model):
    __tablename__ = "ThanhToan"

    MaThanhToan = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MaDatPhong = db.Column(
        db.Integer,
        db.ForeignKey("DatPhong.MaDatPhong", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        unique=True
    )
    PhuongThucThanhToan = db.Column(db.String(50), nullable=False)
    TrangThaiThanhToan = db.Column(db.Integer, nullable=False)
    SoTienThanhToan = db.Column(db.Numeric(18, 2), nullable=False)
    MaGiaoDich = db.Column(db.String(100), nullable=True)
    ThoiGianThanhToan = db.Column(db.DateTime, nullable=True)

    dat_phong = db.relationship(
        "DatPhong",
        back_populates="thanh_toan"
    )

    def __repr__(self):
        return f"<ThanhToan {self.MaThanhToan}>"



# =========================================================
# BẢNG HOÀN TIỀN
#
# TrangThaiHoanTien:
# 0 = Chờ xử lý
# 1 = Thành công
# 2 = Thất bại
# =========================================================
class HoanTien(db.Model):
    __tablename__ = "HoanTien"

    MaHoanTien = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MaDatPhong = db.Column(
        db.Integer,
        db.ForeignKey("DatPhong.MaDatPhong", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        unique=True
    )
    SoTienHoan = db.Column(db.Numeric(18, 2), nullable=False)
    LyDoHoanTien = db.Column(db.String(255), nullable=True)
    TrangThaiHoanTien = db.Column(db.Integer, nullable=False)
    ThoiGianHoanTien = db.Column(db.DateTime, nullable=True)

    dat_phong = db.relationship(
        "DatPhong",
        back_populates="hoan_tien"
    )

    def __repr__(self):
        return f"<HoanTien {self.MaHoanTien}>"



# =========================================================
# BẢNG ĐÁNH GIÁ
# =========================================================
class DanhGia(db.Model):
    __tablename__ = "DanhGia"

    MaDanhGia = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MaDatPhong = db.Column(
        db.Integer,
        db.ForeignKey("DatPhong.MaDatPhong", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        unique=True
    )
    MaNguoiDung = db.Column(
        db.Integer,
        db.ForeignKey("NguoiDung.MaNguoiDung", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False
    )
    MaKhachSan = db.Column(
        db.Integer,
        db.ForeignKey("KhachSan.MaKhachSan", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False
    )
    SoSao = db.Column(db.Integer, nullable=False)
    BinhLuan = db.Column(db.Text, nullable=True)
    NgayDanhGia = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    dat_phong = db.relationship(
        "DatPhong",
        back_populates="danh_gia"
    )

    nguoi_dung = db.relationship(
        "NguoiDung",
        back_populates="danh_gias"
    )

    khach_san = db.relationship(
        "KhachSan",
        back_populates="danh_gias"
    )

    def __repr__(self):
        return f"<DanhGia {self.MaDanhGia}>"



# =========================================================
# BẢNG CHUYỂN TIỀN CHO KHÁCH SẠN
#
# TrangThaiChuyenTien:
# 0 = Chờ chuyển tiền
# 1 = Đã chuyển
# 2 = Thất bại
# =========================================================
class ChuyenTienKhachSan(db.Model):
    __tablename__ = "ChuyenTienKhachSan"

    MaChuyenTien = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MaDatPhong = db.Column(
        db.Integer,
        db.ForeignKey("DatPhong.MaDatPhong", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        unique=True
    )
    MaKhachSan = db.Column(
        db.Integer,
        db.ForeignKey("KhachSan.MaKhachSan", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False
    )
    TongTienDonHang = db.Column(db.Numeric(18, 2), nullable=False)
    PhiHeThong = db.Column(db.Numeric(18, 2), nullable=False)
    SoTienChuyenChoKhachSan = db.Column(db.Numeric(18, 2), nullable=False)
    TrangThaiChuyenTien = db.Column(db.Integer, nullable=False)
    ThoiGianChuyenTien = db.Column(db.DateTime, nullable=True)

    dat_phong = db.relationship(
        "DatPhong",
        back_populates="chuyen_tien_khach_san"
    )

    khach_san = db.relationship(
        "KhachSan",
        back_populates="chuyen_tien_khach_sans"
    )

    def __repr__(self):
        return f"<ChuyenTienKhachSan {self.MaChuyenTien}>"