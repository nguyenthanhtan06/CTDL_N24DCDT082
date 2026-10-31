# DT067 — Tính giá trị biểu thức hậu tố bằng ngăn xếp

Sinh viên: Nguyễn Thành Tân · N24DCDT082 · INT13185 · Nhóm 03.

## Cài đặt và chạy
Cần Python 3.12 trở lên. Tại thư mục có app.py:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Kiểm thử

```powershell
python -m unittest -v test_postfix.py
python -c "import app; d=app.run_test_suite(); print(d.to_string(index=False))"
```

Đã kiểm tại commit `17d0a9c68d8b915fa9d0327eecef36e57efa552a`: dashboard 12/12 PASS; unittest 5/5 phương thức PASS (12 subTest độc lập). Log tại `test-results.txt` và `clone-S-test-results.txt`.

## Hồ sơ và ảnh minh chứng

- Báo cáo Word: `N24DCDT082_DT067_NguyenThanhTan_BaoCao.docx`
- Báo cáo PDF: `N24DCDT082_DT067_NguyenThanhTan_BaoCao.pdf` (46 trang, xuất ngày 31/10/2026)
- ZIP mã nguồn và TXT thông tin nộp ở thư mục gốc.
- A01–A11 trong `docs/anh_ket_qua/`. A10 là ảnh clone sạch. A11 ghi lại trạng thái repo riêng tư tại thời điểm chụp; repo hiện công khai.

## GitHub

Repo công khai: https://github.com/nguyenthanhtan06/CTDL_N24DCDT082

Mã, ZIP và báo cáo được đối chiếu theo commit C/S `17d0a9c68d8b915fa9d0327eecef36e57efa552a`. SHA-256 và permalink nằm trong tệp `N24DCDT082_DT067_NguyenThanhTan_ThongTinNop.txt`.