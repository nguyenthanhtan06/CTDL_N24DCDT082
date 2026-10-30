# DT067 — Tính giá trị biểu thức hậu tố bằng ngăn xếp

Sinh viên: Nguyễn Thành Tân · N24DCDT082 · INT13185 · Nhóm 03.

## Cài đặt và chạy

Cần Python 3.12 trở lên. Tại thư mục chứa `app.py`:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Kiểm thử

```powershell
python -m unittest -v test_postfix.py
python -c "import app; app.run_test_suite()"
```

Đã kiểm clone sạch tại commit `17d0a9c68d8b915fa9d0327eecef36e57efa552a`: dashboard 12/12 PASS; unittest 5/5 phương thức PASS (12 subTest độc lập). Chi tiết ở `clone-S-test-results.txt` và `test-results.txt`.

## Ảnh minh chứng

A01–A09 nằm trong `docs/anh_ket_qua/`. A10/A11 chưa có ảnh chụp; không dùng ảnh giả. A10 có log clone kiểm thử.

## GitHub

Repo: https://github.com/nguyenthanhtan06/CTDL_N24DCDT082 (đang riêng tư). Gói ZIP đồng bộ với `app.py`; SHA-256 và các permalink nằm trong `N24DCDT082_DT067_NguyenThanhTan_ThongTinNop.txt`. Cần cấp quyền cho giảng viên nếu họ cần mở repo.
