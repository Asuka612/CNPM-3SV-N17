function checkStock() {
        var select = document.getElementById('thuocSelect');
        var stock = parseFloat(select.options[select.selectedIndex].getAttribute('data-stock') || 0);

        var lieu = parseFloat(document.getElementById('lieuDung').value || 0);
        var ngay = parseFloat(document.getElementById('soNgay').value || 0);

        // Làm tròn lên giống backend
        var total = Math.ceil(lieu * ngay);

        document.getElementById('totalPreview').innerText = total;

        var warning = document.getElementById('stockWarning');
        var btn = document.getElementById('btnSubmit');

        if (total > stock) {
            warning.style.display = 'inline';
            btn.disabled = true; // Khóa nút submit
        } else {
            warning.style.display = 'none';
            btn.disabled = false;
        }
    }