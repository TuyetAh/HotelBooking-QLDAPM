//điều khiển dropdown và slider
document.addEventListener("DOMContentLoaded", function () {
    // =========================
    // 1. Bộ chọn người lớn / phòng
    // =========================
    const guestRoomDisplay = document.getElementById("guestRoomDisplay");
    const guestRoomDropdown = document.getElementById("guestRoomDropdown");
    const guestRoomDone = document.getElementById("guestRoomDone");
    const guestRoomSummary = document.getElementById("guestRoomSummary");
    const guestRoomArrow = document.getElementById("guestRoomArrow");

    const adultMinus = document.getElementById("adultMinus");
    const adultPlus = document.getElementById("adultPlus");
    const roomMinus = document.getElementById("roomMinus");
    const roomPlus = document.getElementById("roomPlus");

    const adultCount = document.getElementById("adultCount");
    const roomCount = document.getElementById("roomCount");

    const adultInput = document.getElementById("adultInput");
    const roomInput = document.getElementById("roomInput");

    let adults = parseInt(adultInput?.value || "2");
    let rooms = parseInt(roomInput?.value || "1");

    function updateGuestRoomSummary() {
        if (guestRoomSummary) {
            guestRoomSummary.textContent = `${adults} người lớn, ${rooms} phòng`;
        }

        if (adultCount) adultCount.textContent = adults;
        if (roomCount) roomCount.textContent = rooms;

        if (adultInput) adultInput.value = adults;
        if (roomInput) roomInput.value = rooms;

        if (adultMinus) adultMinus.disabled = adults <= 1;
        if (roomMinus) roomMinus.disabled = rooms <= 1;
    }

    function toggleGuestDropdown(show) {
        if (!guestRoomDropdown || !guestRoomArrow) return;

        if (show) {
            guestRoomDropdown.classList.add("show");
            guestRoomArrow.classList.remove("fa-angle-up");
            guestRoomArrow.classList.add("fa-angle-down");
        } else {
            guestRoomDropdown.classList.remove("show");
            guestRoomArrow.classList.remove("fa-angle-down");
            guestRoomArrow.classList.add("fa-angle-up");
        }
    }

    if (guestRoomDisplay) {
        guestRoomDisplay.addEventListener("click", function (e) {
            e.stopPropagation();
            const isOpen = guestRoomDropdown.classList.contains("show");
            toggleGuestDropdown(!isOpen);
        });
    }

    if (guestRoomDone) {
        guestRoomDone.addEventListener("click", function () {
            toggleGuestDropdown(false);
        });
    }

    if (adultPlus) {
        adultPlus.addEventListener("click", function () {
            adults++;
            updateGuestRoomSummary();
        });
    }

    if (adultMinus) {
        adultMinus.addEventListener("click", function () {
            if (adults > 1) adults--;
            updateGuestRoomSummary();
        });
    }

    if (roomPlus) {
        roomPlus.addEventListener("click", function () {
            rooms++;
            updateGuestRoomSummary();
        });
    }

    if (roomMinus) {
        roomMinus.addEventListener("click", function () {
            if (rooms > 1) rooms--;
            updateGuestRoomSummary();
        });
    }

    document.addEventListener("click", function (e) {
        if (
            guestRoomDropdown &&
            guestRoomDisplay &&
            !guestRoomDropdown.contains(e.target) &&
            !guestRoomDisplay.contains(e.target)
        ) {
            toggleGuestDropdown(false);
        }
    });

    updateGuestRoomSummary();

    // =========================
    // 2. Slider khách sạn nổi bật
    // =========================
    const track = document.getElementById("featuredSliderTrack");
    const prevBtn = document.getElementById("featuredPrev");
    const nextBtn = document.getElementById("featuredNext");

    if (track && prevBtn && nextBtn) {
        const slides = track.querySelectorAll(".featured-slide");
        let currentIndex = 0;

        function getVisibleCount() {
            if (window.innerWidth <= 768) return 1;
            if (window.innerWidth <= 1100) return 2;
            return 4;
        }

        function updateSlider() {
            const visibleCount = getVisibleCount();
            const totalSlides = slides.length;

            if (totalSlides === 0) {
                prevBtn.disabled = true;
                nextBtn.disabled = true;
                return;
            }

            const slideWidth = slides[0].offsetWidth;
            const gap = 18;
            const offset = currentIndex * (slideWidth + gap);

            track.style.transform = `translateX(-${offset}px)`;

            prevBtn.disabled = currentIndex <= 0;
            nextBtn.disabled = currentIndex >= totalSlides - visibleCount;
        }

        nextBtn.addEventListener("click", function () {
            const visibleCount = getVisibleCount();
            const totalSlides = slides.length;

            if (currentIndex < totalSlides - visibleCount) {
                currentIndex++;
                updateSlider();
            }
        });

        prevBtn.addEventListener("click", function () {
            if (currentIndex > 0) {
                currentIndex--;
                updateSlider();
            }
        });

        window.addEventListener("resize", function () {
            const visibleCount = getVisibleCount();
            const totalSlides = slides.length;

            if (currentIndex > totalSlides - visibleCount) {
                currentIndex = Math.max(0, totalSlides - visibleCount);
            }

            updateSlider();
        });

        updateSlider();
    }
});


// =========================
// 3. Validate ngày (>= hôm nay & ở tối thiểu 1 đêm)
// =========================
document.addEventListener("DOMContentLoaded", function () {
    const checkinInputs = document.querySelectorAll("input[name='checkin']");
    const checkoutInputs = document.querySelectorAll("input[name='checkout']");

    const today = new Date();
    const formatDate = (date) => {
        return date.toISOString().split("T")[0];
    };

    const todayStr = formatDate(today);

    checkinInputs.forEach((checkinInput, index) => {
        const checkoutInput = checkoutInputs[index];
        if (!checkoutInput) return;

        // Không cho chọn ngày quá khứ
        checkinInput.min = todayStr;
        checkoutInput.min = todayStr;

        // Khi chọn checkin
        checkinInput.addEventListener("change", function () {
            if (!checkinInput.value) return;

            const checkinDate = new Date(checkinInput.value);

            // checkout = checkin + 1 ngày
            const minCheckoutDate = new Date(checkinDate);
            minCheckoutDate.setDate(minCheckoutDate.getDate() + 1);

            const minCheckoutStr = formatDate(minCheckoutDate);

            checkoutInput.min = minCheckoutStr;

            // nếu checkout không hợp lệ thì reset
           if (checkoutInput.value && checkoutInput.value < minCheckoutStr) {
                checkoutInput.value = "";
            }
        });

        // Khi chọn checkout
        checkoutInput.addEventListener("change", function () {
            if (!checkinInput.value) return;

            const checkinDate = new Date(checkinInput.value);
            const checkoutDate = new Date(checkoutInput.value);

            const minCheckoutDate = new Date(checkinDate);
            minCheckoutDate.setDate(minCheckoutDate.getDate() + 1);

            if (checkoutDate < minCheckoutDate) {
                alert("Bạn phải đặt tối thiểu 1 đêm.");
                checkoutInput.value = formatDate(minCheckoutDate);
            }
        });
    });
});


// =========================
// 4. Auto submit bộ lọc trang tìm kiếm
// =========================
document.addEventListener("DOMContentLoaded", function () {
    const autoFilterForm = document.getElementById("autoFilterForm");
    if (!autoFilterForm) return;

    const changeInputs = autoFilterForm.querySelectorAll(".auto-submit-change");
    const textInputs = autoFilterForm.querySelectorAll(".auto-submit-input");

    let debounceTimer = null;

    changeInputs.forEach((input) => {
        input.addEventListener("change", function () {
            autoFilterForm.submit();
        });
    });

    textInputs.forEach((input) => {
        input.addEventListener("input", function () {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                autoFilterForm.submit();
            }, 600);
        });
    });
});


// =========================
// 5. Radio có thể click lại để bỏ chọn
// =========================
document.addEventListener("DOMContentLoaded", function () {
    const radios = document.querySelectorAll(".auto-submit-change[type='radio']");

    radios.forEach((radio) => {
        // lưu trạng thái trước đó
        radio.dataset.checked = radio.checked;

        radio.addEventListener("click", function (e) {
            // nếu đã chọn rồi thì bỏ chọn
            if (this.dataset.checked === "true") {
                this.checked = false;
                this.dataset.checked = "false";

                // submit lại form
                const form = document.getElementById("autoFilterForm");
                if (form) form.submit();

                e.preventDefault(); // chặn hành vi mặc định
            } else {
                // reset tất cả radio cùng name
                document.querySelectorAll(`input[name="${this.name}"]`).forEach(r => {
                    r.dataset.checked = "false";
                });

                this.dataset.checked = "true";
            }
        });

        // cập nhật trạng thái khi change (quan trọng)
        radio.addEventListener("change", function () {
            document.querySelectorAll(`input[name="${this.name}"]`).forEach(r => {
                r.dataset.checked = "false";
            });

            this.dataset.checked = "true";
        });
    });
});

// =========================
// 6.slider ảnh loại phòng
// =========================
document.addEventListener("DOMContentLoaded", function () {
    const roomSliders = document.querySelectorAll(".room-slider");

    roomSliders.forEach((slider) => {
        const images = slider.querySelectorAll(".room-slide-img");
        const prevBtn = slider.querySelector(".room-prev");
        const nextBtn = slider.querySelector(".room-next");
        const currentText = slider.querySelector(".current-room-slide");

        if (!images.length) return;

        let currentIndex = 0;

        function showImage(index) {
            images.forEach((img) => img.classList.remove("active"));

            if (index < 0) index = images.length - 1;
            if (index >= images.length) index = 0;

            currentIndex = index;
            images[currentIndex].classList.add("active");

            if (currentText) {
                currentText.textContent = currentIndex + 1;
            }
        }

        if (prevBtn) {
            prevBtn.addEventListener("click", function () {
                showImage(currentIndex - 1);
            });
        }

        if (nextBtn) {
            nextBtn.addEventListener("click", function () {
                showImage(currentIndex + 1);
            });
        }

        showImage(0);
    });
});
// =========================
//7. MODAL xem tất cả ảnh KS
// =========================
document.addEventListener("DOMContentLoaded", function () {
    const openBtn = document.getElementById("openHotelGallery");
    const closeBtn = document.getElementById("closePhotoViewer");
    const viewer = document.getElementById("hotelPhotoViewer");

    const mainImage = document.getElementById("photoViewerImage");
    const titleText = document.getElementById("photoViewerTitle");
    const counterText = document.getElementById("photoViewerCounter");

    const prevBtn = document.getElementById("photoPrev");
    const nextBtn = document.getElementById("photoNext");
    const thumbs = document.querySelectorAll(".photo-thumb");

    if (!openBtn || !closeBtn || !viewer || !mainImage || thumbs.length === 0) return;

    let currentIndex = 0;

    function showPhoto(index) {
        if (index < 0) index = thumbs.length - 1;
        if (index >= thumbs.length) index = 0;

        currentIndex = index;

        const thumb = thumbs[currentIndex];
        const src = thumb.dataset.src;
        const title = thumb.dataset.title;

        mainImage.src = src;
        titleText.textContent = title || "Hình khách sạn";
        counterText.textContent = `${currentIndex + 1}/${thumbs.length}`;

        thumbs.forEach(t => t.classList.remove("active"));
        thumb.classList.add("active");

        thumb.scrollIntoView({
            behavior: "smooth",
            inline: "center",
            block: "nearest"
        });
    }

    openBtn.addEventListener("click", function () {
        viewer.classList.add("show");
        document.body.style.overflow = "hidden";
        showPhoto(0);
    });

    closeBtn.addEventListener("click", function () {
        viewer.classList.remove("show");
        document.body.style.overflow = "";
    });

    prevBtn.addEventListener("click", function () {
        showPhoto(currentIndex - 1);
    });

    nextBtn.addEventListener("click", function () {
        showPhoto(currentIndex + 1);
    });

    thumbs.forEach((thumb) => {
        thumb.addEventListener("click", function () {
            showPhoto(Number(this.dataset.index));
        });
    });

    document.addEventListener("keydown", function (e) {
        if (!viewer.classList.contains("show")) return;

        if (e.key === "Escape") {
            viewer.classList.remove("show");
            document.body.style.overflow = "";
        }

        if (e.key === "ArrowLeft") {
            showPhoto(currentIndex - 1);
        }

        if (e.key === "ArrowRight") {
            showPhoto(currentIndex + 1);
        }
    });
});

// =========================
// 8. Thôngbaso tắt sau 3 giây
// =========================
setTimeout(() => {
    document.querySelectorAll('.alert').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(-10px)';
        setTimeout(() => el.remove(), 300);
    });
}, 3000);

// 9. LỌC NHANH trong qly loại phòng
document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("roomSearchInput");
    const statusFilter = document.getElementById("roomStatusFilter");
    const rows = document.querySelectorAll(".room-row");

    if (!searchInput || !statusFilter || rows.length === 0) return;

    function filterRows() {
        const keyword = searchInput.value.toLowerCase().trim();
        const status = statusFilter.value;

        rows.forEach((row) => {
            const text = row.innerText.toLowerCase();
            const rowStatus = row.dataset.status;

            const matchKeyword = text.includes(keyword);
            const matchStatus = status === "all" || rowStatus === status;

            row.style.display = matchKeyword && matchStatus ? "" : "none";
        });
    }

    searchInput.addEventListener("input", filterRows);
    statusFilter.addEventListener("change", filterRows);
});

// 10. Lưu ảnh khi thêm ảnh của trang chínhualoaiphong
document.addEventListener("DOMContentLoaded", function () {
    const imageInput = document.querySelector("input[name='room_images']");
    const editRoomForm = document.getElementById("editRoomForm");

    if (!imageInput || !editRoomForm) return;

    imageInput.addEventListener("change", function () {
        if (imageInput.files.length > 0) {
            editRoomForm.submit();
        }
    });
});
// 11. Khi ấn xemm đơn của các phògn đang có ng ở sẽ xổ đơn ngay bên dưới nó
document.addEventListener("DOMContentLoaded", function () {
    const buttons = document.querySelectorAll(".toggle-room-orders");

    buttons.forEach(btn => {
        btn.addEventListener("click", function () {
            const targetId = this.dataset.target;
            const row = document.getElementById(targetId);

            if (!row) return;

            row.classList.toggle("show");

            this.textContent = row.classList.contains("show")
                ? "Ẩn đơn"
                : "Xem đơn";
        });
    });
});
// 12. Tool bả chỉ xuất hiện khi ấn vào tab đơn đặt
document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("bookingSearchInput");
    const statusFilter = document.getElementById("bookingStatusFilter");
    const rows = document.querySelectorAll(".booking-row");

    if (!searchInput || !statusFilter || rows.length === 0) return;

    function filterBookings() {
        const keyword = searchInput.value.trim().replace("#", "");
        const status = statusFilter.value;

        rows.forEach((row) => {
            const code = row.dataset.bookingCode || "";
            const rowStatus = row.dataset.status || "";

            const matchCode = code.includes(keyword);
            const matchStatus = status === "all" || rowStatus === status;

            row.style.display = matchCode && matchStatus ? "" : "none";
        });
    }

    searchInput.addEventListener("input", filterBookings);
    statusFilter.addEventListener("change", filterBookings);
});

// 13. khi chọn ảnh sẽ hiển thị preview ngay, có thể xóa ảnh trước khi submit
document.addEventListener("DOMContentLoaded", function () {
    const input = document.getElementById("addRoomImagesInput");
    const previewBox = document.getElementById("addRoomImagePreview");
    const emptyBox = document.getElementById("addRoomEmptyImageBox");

    if (!input || !previewBox) return;

    let selectedFiles = new DataTransfer();

    function renderPreview() {
        previewBox.innerHTML = "";

        if (selectedFiles.files.length === 0) {
            previewBox.appendChild(emptyBox);
            return;
        }

        Array.from(selectedFiles.files).forEach((file, index) => {
            const reader = new FileReader();

            reader.onload = function (e) {
                const item = document.createElement("div");
                item.className = "room-image-manage-item";

                item.innerHTML = `
                    <img src="${e.target.result}" alt="Ảnh loại phòng">
                    <button type="button" class="btn-delete-image" data-index="${index}">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                `;

                previewBox.appendChild(item);
            };

            reader.readAsDataURL(file);
        });
    }

    input.addEventListener("change", function () {
        Array.from(input.files).forEach(file => {
            selectedFiles.items.add(file);
        });

        input.files = selectedFiles.files;
        renderPreview();
    });

    previewBox.addEventListener("click", function (e) {
        const deleteBtn = e.target.closest(".btn-delete-image");
        if (!deleteBtn) return;

        const removeIndex = Number(deleteBtn.dataset.index);
        const newFiles = new DataTransfer();

        Array.from(selectedFiles.files).forEach((file, index) => {
            if (index !== removeIndex) {
                newFiles.items.add(file);
            }
        });

        selectedFiles = newFiles;
        input.files = selectedFiles.files;

        renderPreview();
    });
});



// 14. tìmkiesm, lọc, tính tổng của table ds chuyển tiền ks
document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("payoutSearchInput");
    const statusFilter = document.getElementById("payoutStatusFilter");
    const rows = document.querySelectorAll(".payout-row");

    const totalOrderEl = document.getElementById("payoutTotalOrder");
    const totalFeeEl = document.getElementById("payoutTotalFee");
    const totalNetEl = document.getElementById("payoutTotalNet");

    if (!searchInput || !statusFilter || rows.length === 0) return;

    function formatMoney(value) {
        return Number(value || 0).toLocaleString("en-US") + "đ";
    }

    function filterPayouts() {
        const keyword = searchInput.value.trim().replace("#", "");
        const selectedStatus = statusFilter.value;

        let totalOrder = 0;
        let totalFee = 0;
        let totalNet = 0;

        rows.forEach((row) => {
            const code = row.dataset.bookingCode || "";
            const status = row.dataset.status || "";

            const matchCode = keyword === "" || code.includes(keyword);
            const matchStatus = selectedStatus === "all" || status === selectedStatus;

            const isVisible = matchCode && matchStatus;
            row.style.display = isVisible ? "" : "none";

            if (isVisible) {
                totalOrder += Number(row.dataset.total || 0);
                totalFee += Number(row.dataset.fee || 0);
                totalNet += Number(row.dataset.net || 0);
            }
        });

        totalOrderEl.textContent = formatMoney(totalOrder);
        totalFeeEl.textContent = "-" + formatMoney(totalFee);
        totalNetEl.textContent = formatMoney(totalNet);
    }

    searchInput.addEventListener("input", filterPayouts);
    statusFilter.addEventListener("change", filterPayouts);

    filterPayouts();
});
// 15. Chọn Loại Phòng theo đơn
document.addEventListener("DOMContentLoaded", function () {
    const bookingSelect = document.getElementById("reviewBookingSelect");
    const roomInput = document.getElementById("reviewRoomId");

    if (!bookingSelect || !roomInput) return;

    bookingSelect.addEventListener("change", function () {
        const selectedOption = bookingSelect.options[bookingSelect.selectedIndex];
        roomInput.value = selectedOption.dataset.roomId || "";
    });
});
// 16. Slider ảnh lp của trang đặt phòng

document.addEventListener("DOMContentLoaded", function () {
   const track = document.getElementById("bookingRoomGalleryTrack");
   const prevBtn = document.getElementById("bookingRoomPrev");
   const nextBtn = document.getElementById("bookingRoomNext");


   if (!track || !prevBtn || !nextBtn) return;


   const items = track.querySelectorAll(".booking-room-gallery-item");
   let currentIndex = 0;


   function updateGallery() {
       if (!items.length) return;


       const itemWidth = items[0].offsetWidth;
       const gap = 14;
       const visibleCount = 3;
       const maxIndex = Math.max(0, items.length - visibleCount);


       if (currentIndex < 0) currentIndex = 0;
       if (currentIndex > maxIndex) currentIndex = maxIndex;


       track.style.transform = `translateX(-${currentIndex * (itemWidth + gap)}px)`;


       prevBtn.disabled = currentIndex === 0;
       nextBtn.disabled = currentIndex === maxIndex;
   }


   nextBtn.addEventListener("click", function () {
       currentIndex++;
       updateGallery();
   });


   prevBtn.addEventListener("click", function () {
       currentIndex--;
       updateGallery();
   });


   window.addEventListener("resize", updateGallery);


   updateGallery();
});


//17. Đếm nguọc 3p cho giữu phòng ở trang datphong
document.addEventListener("DOMContentLoaded", function () {
   const countdownEl = document.getElementById("bookingHoldCountdown");
   if (!countdownEl) return;


   let totalSeconds = 3 * 60;
   const bookingId = countdownEl.dataset.bookingId;


   const timer = setInterval(function () {
       const minutes = Math.floor(totalSeconds / 60);
       const seconds = totalSeconds % 60;


       countdownEl.textContent =
           String(minutes).padStart(2, "0") + ":" + String(seconds).padStart(2, "0");


       if (totalSeconds <= 0) {
           clearInterval(timer);
           window.location.href = `/dat-phong/${bookingId}/het-han`;
       }


       totalSeconds--;
   }, 1000);
});


document.addEventListener("DOMContentLoaded", function () {
   const countdownEl = document.getElementById("momoCountdown");
   if (!countdownEl) return;


   let totalSeconds = 5 * 60;
   const bookingId = countdownEl.dataset.bookingId;


   const timer = setInterval(function () {
       const minutes = Math.floor(totalSeconds / 60);
       const seconds = totalSeconds % 60;


       countdownEl.textContent =
           String(minutes).padStart(2, "0") + ":" + String(seconds).padStart(2, "0");


       if (totalSeconds <= 0) {
           clearInterval(timer);
           window.location.href = `/dat-phong/${bookingId}/het-han`;
       }


       totalSeconds--;
   }, 1000);
});

