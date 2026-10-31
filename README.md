# DT067 - Tính giá trị biểu thức hậu tố bằng ngăn xếp

Sinh viên: Nguyễn Thành Tân - N24DCDT082 - INT13185 - D24CQDT01-N, Nhóm 03.

## Clone và chạy ứng dụng

Mở PowerShell, chạy các lệnh sau:

```powershell
git clone https://github.com/nguyenthanhtan06/CTDL_N24DCDT082.git
cd CTDL_N24DCDT082
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Nếu đã tải repo hoặc giải nén ZIP mã nguồn, mở PowerShell tại thư mục có file `app.py`, sau đó chạy:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Dùng `python -m streamlit` để chạy bằng đúng bản Python đã cài thư viện. Sau khi khởi động, mở địa chỉ localhost hiện trong PowerShell.

## Kiểm thử

```powershell
python -m unittest -v test_postfix.py
python -c "import app; d=app.run_test_suite(); print(d.to_string(index=False))"
```

Đã kiểm tại commit mã nguồn `17d0a9c68d8b915fa9d0327eecef36e57efa552a`: dashboard 12/12 PASS; unittest 5/5 phương thức PASS (12 subTest độc lập). Log tại `test-results.txt` và `clone-S-test-results.txt`.

## Hồ sơ và ảnh minh chứng

- Báo cáo Word: `N24DCDT082_DT067_NguyenThanhTan_BaoCao.docx`
- Báo cáo PDF: `N24DCDT082_DT067_NguyenThanhTan_BaoCao.pdf` (46 trang)
- ZIP mã nguồn: `N24DCDT082_DT067_NguyenThanhTan_MaNguon.zip`
- Thông tin nộp: `N24DCDT082_DT067_NguyenThanhTan_ThongTinNop.txt`
- Ảnh A01-A11 tại `docs/anh_ket_qua/`. A10 là ảnh clone sạch. A11 ghi lại trạng thái repo riêng tư tại thời điểm chụp; repo hiện công khai.

Repo công khai: https://github.com/nguyenthanhtan06/CTDL_N24DCDT082
SHA-256 và permalink nằm trong tệp thông tin nộp.
