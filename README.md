# DT067 — Tính giá trị biểu thức hậu tố bằng ngăn xếp

Sinh viên: Nguyễn Thành Tân · N24DCDT082 · INT13185 · Nhóm 03.

## Cài đặt và chạy
Cần Python 3.12 trở lên. Tại thư mục có app.py:
python -m pip install -r requirements.txt
python -m streamlit run app.py

## Kiểm thử
python -m unittest -v test_postfix.py
python -c "import app; d=app.run_test_suite(); print(d.to_string(index=False))"

Clone commit 17d0a9c68d8b915fa9d0327eecef36e57efa552a: dashboard 12/12 PASS; unittest 5/5 phương thức PASS (12 subTest độc lập). Chi tiết tại test-results.txt và clone-S-test-results.txt.

## Ảnh minh chứng
A01–A11 trong docs/anh_ket_qua/. A10 là ảnh clone sạch; A11 là ảnh repo/commit GitHub thật.

## GitHub
Repo: https://github.com/nguyenthanhtan06/CTDL_N24DCDT082 (riêng tư). ZIP đồng bộ với app.py; SHA-256 và permalink trong tệp ThongTinNop. Cần cấp quyền cho giảng viên nếu họ cần truy cập.
