document.addEventListener('DOMContentLoaded', function() {
    const dateInput = document.getElementById('day');
    const timeHelp = document.getElementById('timeHelp');

    // 1. Khởi tạo Flatpickr cho ô chọn giờ
    // Biến timePicker giúp ta cập nhật lại giờ min/max sau này
    const timePicker = flatpickr("#time", {
        enableTime: true,
        noCalendar: true,
        dateFormat: "H:i", // Bắt buộc định dạng 24h (H viết hoa)
        time_24hr: true,   // Bật chế độ 24h
        minTime: "08:00",
        maxTime: "17:00",
        minuteIncrement: 30 // (Tùy chọn) Chỉ cho chọn chẵn 30 phút cho đẹp
    });

    // 2. Chặn ngày quá khứ
    const todayISO = new Date().toISOString().split('T')[0];
    dateInput.min = todayISO;

    // 3. Hàm xử lý logic thời gian
    function updateTimeConstraints() {
        if (!dateInput.value) return;

        const openTime = "08:00";
        const closeTime = "17:00";

        const now = new Date();
        const selectedDate = new Date(dateInput.value);
        const todayDate = new Date();

        todayDate.setHours(0, 0, 0, 0);
        selectedDate.setHours(0, 0, 0, 0);

        if (selectedDate.getTime() === todayDate.getTime()) {
            // --- NẾU LÀ HÔM NAY ---

            // Tính giờ hiện tại + 30 phút
            let minBookingTime = new Date(now.getTime() + 30 * 60000);

            let hours = minBookingTime.getHours().toString().padStart(2, '0');
            let minutes = minBookingTime.getMinutes().toString().padStart(2, '0');
            let minTimeStr = `${hours}:${minutes}`;

            // Cập nhật Flatpickr
            if (minTimeStr > openTime) {
                // Nếu quá giờ đóng cửa
                if (minTimeStr > closeTime) {
                    timePicker.set('minTime', closeTime); // Khóa
                    timePicker.clear(); // Xóa giá trị cũ
                    document.getElementById('time').disabled = true;
                    if (timeHelp) timeHelp.innerText = "Đã hết giờ làm việc hôm nay.";
                } else {
                    // Cập nhật giờ tối thiểu mới cho Flatpickr
                    timePicker.set('minTime', minTimeStr);
                    document.getElementById('time').disabled = false;
                    if (timeHelp) timeHelp.innerText = `Cần đặt trước 30p. Sớm nhất: ${minTimeStr} hoặc quay lại vào ngày mai.`;
                }
            } else {
                // Vẫn trong buổi sáng sớm -> Reset về 08:00
                timePicker.set('minTime', openTime);
                document.getElementById('time').disabled = false;
                if (timeHelp) timeHelp.innerText = "";
            }

        } else {
            // --- NẾU LÀ NGÀY KHÁC ---
            timePicker.set('minTime', openTime);
            document.getElementById('time').disabled = false;
            if (timeHelp) timeHelp.innerText = "";
        }
    }

    // Gắn sự kiện khi đổi ngày
    dateInput.addEventListener('change', updateTimeConstraints);
});