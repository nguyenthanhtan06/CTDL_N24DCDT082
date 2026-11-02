"""DT067 — Trực quan hóa tính giá trị biểu thức hậu tố bằng ngăn xếp."""
from __future__ import annotations

import html
import re
from typing import Any

import pandas as pd
import streamlit as st


TRACE_COLUMNS = ["Bước", "Token", "Thao tác", "b (Phải)", "a (Trái)", "Phép tính", "Stack sau thao tác", "Ghi chú"]
MAX_TOKENS = 50
MAX_INPUT_ABS = 100
MAX_EXPONENT = 10
INT128_MIN = -(2 ** 127)
INT128_MAX = (2 ** 127) - 1
TEST_CASES = [
    ("VD01", "5 6 2 + * 12 4 / -", 37),
    ("VD02", "2 3 2 ^ ^", 512),
    ("TK01", "8 3 -", 5),
    ("TK02", "3 8 -", -5),
    ("BIEN01", "7 2 /", 3),
    ("BIEN02", "0 7 - 2 /", -3),
    ("BIEN03", "100 0 ^", 1),
    ("LOI01", "4 0 /", "Lỗi chia cho 0"),
    ("KT09", "1 +", "Lỗi thiếu toán hạng"),
    ("KT10", "2 3", "Lỗi dư toán hạng"),
    ("KT11", "2 x +", "Lỗi token không hợp lệ"),
    ("KT12", "100 10 ^ 100 10 ^ *", "Lỗi tràn Int128"),
]

CASE_LABELS = {
    "VD01": "Ví dụ phiếu · 37",
    "VD02": "Lũy thừa phải · 512",
    "TK01": "Trừ · 5",
    "TK02": "Kết quả âm · -5",
    "BIEN01": "Chia dương · 3",
    "BIEN02": "Chia âm · -3",
    "BIEN03": "Số mũ 0 · 1",
    "LOI01": "Chia cho 0 · lỗi",
    "KT09": "Thiếu toán hạng · lỗi",
    "KT10": "Dư toán hạng · lỗi",
    "KT11": "Token sai · lỗi",
    "KT12": "Tràn Int128 · lỗi",
}

# Danh sách mẫu luôn lấy trực tiếp từ cùng bộ dữ liệu với bảng kiểm thử,
# tránh trường hợp dropdown và 12 ca trên dashboard bị lệch nhau.
EXAMPLES = {
    f"{case_id} · {CASE_LABELS[case_id]}": expression
    for case_id, expression, _expected in TEST_CASES
}
EXAMPLES.update({
    "Giáo trình Ví dụ 5.3 · kết quả 9": "3 4 2 * + 1 1 + -",
    "Giáo trình Ví dụ 5.3 · kết quả 15": "2 3 + 4 1 - *",
})


def trunc_div(a: int, b: int) -> int:
    """Chia số nguyên cắt về 0 chính xác, không chuyển sang Float64."""
    if b == 0:
        raise ZeroDivisionError("Chia cho 0.")
    q = abs(a) // abs(b)
    return -q if (a < 0) != (b < 0) else q


def infix_to_postfix(expression: str) -> str:
    """Convert a conventional infix expression to postfix without eval().

    Supports non-negative integer operands, parentheses and + - * / ^.
    Exponentiation is right-associative, matching the DT067 postfix examples.
    """
    compact = re.sub(r"\s+", "", expression)
    tokens = re.findall(r"\d+|[()+\-*/^]", compact)
    if not compact or "".join(tokens) != compact:
        raise ValueError("Biểu thức trung tố có ký tự không hợp lệ. Dùng số nguyên, ngoặc và + - * / ^.")

    precedence = {"+": 1, "-": 1, "*": 2, "/": 2, "^": 3}
    output: list[str] = []
    operators: list[str] = []
    expecting_operand = True
    for token in tokens:
        if token.isdigit():
            if not expecting_operand:
                raise ValueError("Thiếu toán tử giữa hai số trong biểu thức trung tố.")
            output.append(token)
            expecting_operand = False
        elif token == "(":
            if not expecting_operand:
                raise ValueError("Thiếu toán tử trước dấu ngoặc mở.")
            operators.append(token)
        elif token == ")":
            if expecting_operand:
                raise ValueError("Thiếu toán hạng trước dấu ngoặc đóng.")
            while operators and operators[-1] != "(":
                output.append(operators.pop())
            if not operators:
                raise ValueError("Dấu ngoặc đóng không có ngoặc mở tương ứng.")
            operators.pop()
            expecting_operand = False
        else:
            if expecting_operand:
                raise ValueError(f"Thiếu toán hạng trước toán tử '{token}'.")
            while operators and operators[-1] != "(":
                top = operators[-1]
                if precedence[top] > precedence[token] or (precedence[top] == precedence[token] and token != "^"):
                    output.append(operators.pop())
                else:
                    break
            operators.append(token)
            expecting_operand = True

    if expecting_operand:
        raise ValueError("Biểu thức trung tố chưa có toán hạng cuối.")
    if "(" in operators:
        raise ValueError("Thiếu dấu ngoặc đóng trong biểu thức trung tố.")
    output.extend(reversed(operators))
    return " ".join(output)


def normalize_expression(expression: str, mode: str = "Tự nhận dạng") -> str:
    """Return postfix tokens for any supported input mode."""
    if mode == "Hậu tố":
        return expression
    if mode == "Trung tố (tự chuyển)":
        return infix_to_postfix(expression)
    try:
        return infix_to_postfix(expression)
    except ValueError:
        # If it is not valid infix, try it as whitespace-delimited postfix.
        return expression


def evaluate_postfix_with_trace(bt_string: str) -> dict[str, Any]:
    """Đánh giá hậu tố, trả kết quả, stack sau mỗi bước và lịch sử lần vết.

    Token là số nguyên (có thể có dấu) hoặc một trong + - * / ^. Khi gặp
    toán tử, pop b (phải) trước, rồi pop a (trái), đúng quy ước DT067.
    """
    tokens = bt_string.split()
    if not tokens:
        raise ValueError("Biểu thức đang rỗng. Hãy nhập các token cách nhau bằng khoảng trắng.")
    if len(tokens) > MAX_TOKENS:
        raise ValueError(f"Biểu thức có {len(tokens)} token; giới hạn của phiếu là {MAX_TOKENS}.")

    stack: list[int] = []
    trace: list[dict[str, Any]] = []
    snapshots: list[list[int]] = [[]]
    for step, token in enumerate(tokens, start=1):
        if re.fullmatch(r"[+-]?\d+", token):
            value = int(token)
            if abs(value) > MAX_INPUT_ABS:
                raise ValueError(f"Số đầu vào '{token}' ngoài miền -100..100 (mở rộng số âm tùy chọn) tại bước {step}.")
            stack.append(value)
            operation, b, a, calculation, note = "Đẩy số vào ngăn xếp", "—", "—", f"push({value})", "Số nguyên hợp lệ"
        elif token in {"+", "-", "*", "/", "^"}:
            if len(stack) < 2:
                raise ValueError(f"Thiếu toán hạng tại token '{token}' (bước {step}): cần 2 số, stack hiện có {len(stack)}.")
            b = stack.pop()  # Toán hạng phải được lấy trước.
            a = stack.pop()  # Toán hạng trái được lấy sau.
            if token == "+":
                value, calculation = a + b, f"{a} + {b} = {a + b}"
            elif token == "-":
                value, calculation = a - b, f"{a} - {b} = {a - b}"
            elif token == "*":
                value, calculation = a * b, f"{a} × {b} = {a * b}"
            elif token == "/":
                if b == 0:
                    raise ZeroDivisionError(f"Chia cho 0 tại bước {step}: {a} / {b}.")
                value = trunc_div(a, b)  # C++/Julia semantics, không dùng Float64.
                calculation = f"{a} / {b} = {value} (cắt về 0)"
            else:
                if b < 0:
                    raise ValueError(f"Số mũ âm không được hỗ trợ với kiểu số nguyên tại bước {step}.")
                if b > MAX_EXPONENT:
                    raise ValueError(f"Số mũ {b} ngoài miền 0..{MAX_EXPONENT} tại bước {step}.")
                value, calculation = a ** b, f"{a} ^ {b} = {a ** b}"
            if value < INT128_MIN or value > INT128_MAX:
                raise OverflowError(f"Tràn Int128 tại bước {step}: phép tính '{calculation}'.")
            stack.append(value)
            operation = "Lấy b trước, lấy a sau; tính a op b; đẩy kết quả"
            note = "b là toán hạng phải; a là toán hạng trái"
        else:
            raise ValueError(f"Token không hợp lệ '{token}' tại bước {step}. Chỉ chấp nhận số nguyên và + - * / ^.")

        trace.append({"Bước": step, "Token": token, "Thao tác": operation,
                      "b (Phải)": b, "a (Trái)": a, "Phép tính": calculation,
                      "Stack sau thao tác": "[" + ", ".join(map(str, stack)) + "]", "Ghi chú": note})
        snapshots.append(stack.copy())

    if len(stack) != 1:
        raise ValueError(f"Biểu thức dư toán hạng: sau khi đọc hết token còn {len(stack)} giá trị trên stack: {stack}.")
    return {"value": stack[0], "trace": trace, "snapshots": snapshots, "tokens": tokens}


def run_test_suite() -> pd.DataFrame:
    rows = []
    for case_id, expression, expected in TEST_CASES:
        try:
            actual: Any = evaluate_postfix_with_trace(expression)["value"]
            passed = actual == expected
            actual_display = str(actual)
        except ZeroDivisionError:
            actual_display, passed = "Lỗi chia cho 0", expected == "Lỗi chia cho 0"
        except OverflowError:
            actual_display, passed = "Lỗi tràn Int128", expected == "Lỗi tràn Int128"
        except ValueError as exc:
            actual_display = ("Lỗi thiếu toán hạng" if "Thiếu toán hạng" in str(exc)
                              else "Lỗi dư toán hạng" if "dư toán hạng" in str(exc)
                              else "Lỗi token không hợp lệ" if "Token không hợp lệ" in str(exc)
                              else f"Lỗi: {exc}")
            passed = actual_display == expected
        rows.append({"Mã ca": case_id, "Biểu thức hậu tố": expression, "Expected": expected,
                     "Actual": actual_display, "Trạng thái": "PASS" if passed else "FAIL"})
    return pd.DataFrame(rows)



def main():
    st.set_page_config(page_title="Tính giá trị biểu thức hậu tố bằng ngăn xếp", page_icon="🧮", layout="wide", initial_sidebar_state="auto")

    try:
        theme_mode = st.context.theme.type
    except Exception:
        theme_mode = "light"

    if theme_mode == "dark":
        theme_css = """
    :root { color-scheme:dark; background:#000000; }
    html, body { background:#000000 !important; color:#f4f6fb !important; }
    .stApp {
      color-scheme:dark;
      --app-bg:#000000; --app-surface:#111318; --app-text:#f4f6fb;
      --app-muted:#c2c8d2; --app-border:#343943; --app-primary:#a5b4fc;
      --app-primary-soft:#1b1b35; --app-primary-strong-soft:#29264f;
      --app-primary-border:#7772e8; --app-warm-soft:#261a0d;
      --app-warm-border:#8c5a20; --app-slider-track:#48505c;
    }
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"],
    [data-testid="stHeader"], [data-testid="stSidebar"], .block-container {
      background-color:#000000 !important; color:#f4f6fb !important;
    }
    """
    else:
        theme_css = """
    :root { color-scheme:light; background:#ffffff; }
    html, body { background:#ffffff !important; color:#172554 !important; }
    .stApp {
      color-scheme:light;
      --app-bg:#ffffff; --app-surface:#ffffff; --app-text:#172554;
      --app-muted:#475569; --app-border:#cbd5e1; --app-primary:#4f46e5;
      --app-primary-soft:#eef2ff; --app-primary-strong-soft:#e0e7ff;
      --app-primary-border:#a5b4fc; --app-warm-soft:#fff7ed;
      --app-warm-border:#fbbf24; --app-slider-track:#cbd5e1;
    }
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"],
    [data-testid="stHeader"], [data-testid="stSidebar"], .block-container {
      background-color:#ffffff !important; color:#172554 !important;
    }
    """
    st.markdown("""
    <style>
    .stApp {
      --app-bg:var(--background-color,var(--st-background-color,#f4f7fb));
      --app-surface:var(--secondary-background-color,var(--st-secondary-background-color,#ffffff));
      --app-text:var(--text-color,var(--st-text-color,#172554));
      --app-muted:var(--text-color,var(--st-text-color,#475569));
      --app-border:rgba(100,116,139,.34);
      --app-primary:var(--primary-color,var(--st-primary-color,#4f46e5));
      --app-primary-soft:var(--secondary-background-color,var(--st-secondary-background-color,#eef2ff));
      --app-primary-strong-soft:var(--secondary-background-color,var(--st-secondary-background-color,#e0e7ff));
      --app-primary-border:var(--primary-color,var(--st-primary-color,#c7d2fe));
      --app-warm-soft:var(--secondary-background-color,var(--st-secondary-background-color,#fff7ed));
      --app-warm-border:rgba(245,158,11,.58);
      --app-slider-track:var(--secondary-background-color,#cbd5e1);
    }
    @supports (color: color-mix(in srgb, black, white)) {
      .stApp {
        --app-muted:color-mix(in srgb,var(--app-text) 82%,var(--app-bg));
        --app-border:color-mix(in srgb,var(--app-text) 22%,var(--app-bg));
        --app-primary-soft:color-mix(in srgb,var(--app-primary) 15%,var(--app-surface));
        --app-primary-strong-soft:color-mix(in srgb,var(--app-primary) 28%,var(--app-surface));
        --app-primary-border:color-mix(in srgb,var(--app-primary) 62%,var(--app-surface));
        --app-warm-soft:color-mix(in srgb,#f59e0b 12%,var(--app-surface));
        --app-warm-border:color-mix(in srgb,#f59e0b 58%,var(--app-surface));
        --app-slider-track:color-mix(in srgb,var(--app-text) 26%,var(--app-bg));
      }
    }
    html, body, [class*="css"] { font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif; }
    .stApp { background:var(--app-bg)!important; color:var(--app-text); }
    .block-container { max-width:1360px; padding:1.25rem 2rem 4rem; }
    [data-testid="stSidebar"] { min-width:18rem!important; max-width:18rem!important; background:var(--app-surface)!important; border-right:1px solid var(--app-border); color:var(--app-text); }
    [data-testid="stSidebar"] > div:first-child { padding:1.1rem 1rem 1.5rem; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"], [data-testid="stSidebar"] label { color:var(--app-text)!important; }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color:var(--app-muted)!important; }
    h1,h2,h3 { color:var(--app-text); font-family:inherit; letter-spacing:-.025em; }
    h1 { font-size:2.25rem!important; line-height:1.2!important; margin:0 0 .6rem!important; }
    h2 { font-size:1.4rem!important; }
    .stApp label { color:var(--app-text)!important; }
    .stApp [data-testid="stCaptionContainer"] { color:var(--app-muted)!important; }
    .hero { padding:0 0 1.25rem; margin:0 0 1rem; border-bottom:1px solid var(--app-border); }
    .hero h1 { max-width:1100px; }
    .hero p { max-width:72ch; margin:0; color:var(--app-muted); font-size:1rem; line-height:1.55; }
    .identity { display:flex; flex-wrap:wrap; gap:.45rem 1rem; margin-top:.85rem; color:var(--app-text); font-size:.875rem; }
    .identity span { display:inline-flex; gap:.35rem; align-items:baseline; }
    .identity strong { color:var(--app-text); }
    .section-kicker { color:var(--app-primary); font-size:.8rem; font-weight:750; letter-spacing:.045em; margin:0 0 .45rem; }
    .status-strip { display:flex; flex-wrap:wrap; align-items:center; gap:.45rem 1rem; min-height:3.25rem; margin:.4rem 0 1rem; color:var(--app-text); }
    .status-result { color:var(--app-text); font-size:1.5rem; font-weight:750; font-variant-numeric:tabular-nums; }
    .status-label { font-size:.92rem; }
    .status-chip { display:inline-flex; align-items:center; min-height:2rem; padding:.3rem .7rem; border:1px solid var(--app-primary-border); border-radius:999px; background:var(--app-primary-soft); color:var(--app-text); font-size:.875rem; font-weight:650; }
    .content-heading { font-size:1.1rem; font-weight:720; color:var(--app-text); margin:0 0 .2rem; }
    .content-subtitle { color:var(--app-muted); font-size:.9rem; line-height:1.45; margin:0 0 .7rem; }
    .token-rail { display:flex; flex-wrap:wrap; gap:.5rem; padding:.85rem; border:1px solid var(--app-border); border-radius:12px; background:var(--app-surface); }
    .token { min-width:2.65rem; min-height:2.65rem; display:inline-flex; align-items:center; justify-content:center; padding:.45rem .7rem; border:1px solid var(--app-border); border-radius:9px; background:var(--app-surface); color:var(--app-text); font:650 .95rem ui-monospace,SFMono-Regular,Consolas,monospace; font-variant-numeric:tabular-nums; }
    .token.done { background:var(--app-primary-soft); border-color:var(--app-primary-border); color:var(--app-text); }
    .token.active { background:var(--app-primary-strong-soft); border:2px solid var(--app-primary); color:var(--app-text); }
    .token.operator { font-family:ui-monospace,SFMono-Regular,Consolas,monospace; }
    .panel { padding:0; margin:0; background:transparent; border:0; box-shadow:none; }
    .stack-shell { display:flex; align-items:stretch; gap:.9rem; min-height:13rem; max-height:28rem; overflow-y:auto; padding:1rem; border:1px solid var(--app-border); border-radius:12px; background:var(--app-surface); }
    .stack-gauge { align-self:stretch; min-width:3.7rem; display:flex; flex-direction:column; justify-content:space-between; align-items:flex-start; color:var(--app-muted); font-size:.75rem; font-weight:750; letter-spacing:.04em; }
    .stack-cells { width:100%; display:flex; flex-direction:column; align-items:stretch; gap:.45rem; }
    .stack-cell { display:flex; align-items:center; gap:.75rem; min-height:2.7rem; padding:.5rem .75rem; border:1px solid var(--app-border); border-radius:8px; background:var(--app-surface); color:var(--app-text); }
    .stack-cell.top { border:2px solid var(--app-primary); background:var(--app-primary-soft); color:var(--app-text); }
    .stack-pos { width:5.5rem; flex:0 0 auto; color:var(--app-muted); font-size:.75rem; font-weight:700; letter-spacing:.025em; }
    .stack-val { font-size:1.05rem; font-weight:750; font-variant-numeric:tabular-nums; }
    .empty-stack { align-self:center; margin:auto; padding:.75rem 1rem; border:1px dashed var(--app-border); border-radius:8px; color:var(--app-muted); background:var(--app-surface); font-size:.9rem; }
    .op-card { padding:1rem; border:1px solid var(--app-warm-border); border-radius:12px; background:var(--app-warm-soft); color:var(--app-text); }
    .op-badge { color:var(--app-text); background:var(--app-warm-soft); border:1px solid var(--app-warm-border); border-radius:6px; padding:.35rem .55rem; font-size:.875rem; font-weight:750; }
    .calc { margin-top:.85rem; color:var(--app-text); font-size:1.2rem; font-weight:700; overflow-wrap:anywhere; font-variant-numeric:tabular-nums; }
    .hint { color:var(--app-muted); font-size:.9rem; line-height:1.55; margin-top:.5rem; }
    .stButton button, .stDownloadButton button { min-height:44px; border-radius:9px; font-weight:650; transition:border-color .16s ease,background-color .16s ease,color .16s ease; }
    .stButton button:hover, .stDownloadButton button:hover { border-color:var(--app-primary)!important; background:var(--app-primary-soft)!important; color:var(--app-text)!important; }
    button:focus-visible, input:focus-visible, [role="slider"]:focus-visible { outline:3px solid var(--app-primary)!important; outline-offset:2px!important; }
    [data-baseweb="tab-list"] { gap:.25rem; border-bottom:1px solid var(--app-border); overflow-x:auto; }
    [data-baseweb="tab"] { min-height:46px; padding:0 .9rem; color:var(--app-muted); font-weight:650; white-space:nowrap; }
    [aria-selected="true"][data-baseweb="tab"] { color:var(--app-text); }
    div[data-baseweb="tab-highlight"] { background-color:var(--app-primary)!important; }
    [data-testid="stSlider"] [data-rac][data-orientation="horizontal"] > div[data-rac][data-orientation="horizontal"] > div:first-child { background-color:var(--app-slider-track)!important; background-image:none!important; }
    [data-testid="stSlider"] [data-rac][data-orientation="horizontal"] > div[data-rac][data-orientation="horizontal"] > div:nth-child(2) { background-color:var(--app-primary)!important; border-color:var(--app-primary)!important; }
    [data-testid="stSlider"] input[type="range"]:focus-visible + div { outline:3px solid var(--app-primary)!important; outline-offset:3px!important; }
    [data-testid="stDataFrame"] { border:1px solid var(--app-border); border-radius:10px; overflow:hidden; }
    @media(max-width:900px) { .block-container {padding:1rem 1.25rem 3rem;} [data-testid="stSidebar"] {min-width:16rem!important;max-width:16rem!important;} h1 {font-size:1.9rem!important;} }
    @media(max-width:640px) { .block-container {padding:.85rem .85rem 2.5rem;} [data-testid="stSidebar"] {min-width:min(19rem,88vw)!important;max-width:min(19rem,88vw)!important;} h1 {font-size:1.6rem!important;} .hero {padding-bottom:1rem;} .identity {gap:.4rem .8rem;} .stack-shell {min-height:10rem;padding:.75rem;gap:.55rem;} .stack-gauge {min-width:3.25rem;} .stack-pos {width:4.8rem;} .token-rail {gap:.4rem;padding:.65rem;} .token {min-width:2.3rem;min-height:2.5rem;padding:.35rem .55rem;} }
    @media(prefers-reduced-motion:reduce) { *,*::before,*::after {scroll-behavior:auto!important;transition:none!important;animation:none!important;} }
    </style>
    """, unsafe_allow_html=True)
    st.markdown(
        "<style>" + theme_css + """
    .stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stWidgetLabel"],
    .stApp [data-testid="stCaptionContainer"], .stApp label { color:var(--app-text)!important; }
    .stApp [data-testid="stCaptionContainer"] { color:var(--app-muted)!important; }
    .stApp input:not([type="range"]), .stApp textarea,
    .stApp [data-baseweb="select"] > div, .stApp [data-baseweb="input"] > div {
      background-color:var(--app-surface)!important; color:var(--app-text)!important;
      border-color:var(--app-border)!important;
    }
    .stApp input::placeholder, .stApp textarea::placeholder { color:var(--app-muted)!important; opacity:1; }
    [data-baseweb="popover"], [role="listbox"] {
      background-color:var(--app-surface)!important; color:var(--app-text)!important;
    }
    .stApp [data-baseweb="tab"] { color:var(--app-muted)!important; }
    .stApp [aria-selected="true"][data-baseweb="tab"] { color:var(--app-text)!important; }
    </style>""",
        unsafe_allow_html=True,
    )


    def _load_example() -> None:
        st.session_state["expression_input"] = EXAMPLES[st.session_state["example_choice_v2"]]
        st.session_state["input_mode"] = "Tự nhận dạng"

    def _move_step(delta: int) -> None:
        maximum = st.session_state.get("execution_step_max", 0)
        current = st.session_state.get("execution_step", 0)
        st.session_state["execution_step"] = min(max(0, current + delta), maximum)

    # Use a fresh widget key because a browser tab may retain the old sample
    # labels after Streamlit hot-reloads this version of the app.
    if "example_choice_v2" not in st.session_state:
        current_expression = st.session_state.get("expression_input", "")
        st.session_state["example_choice_v2"] = next(
            (label for label, sample in EXAMPLES.items() if sample == current_expression),
            next(iter(EXAMPLES)),
        )
    st.session_state.setdefault("expression_input", EXAMPLES[st.session_state["example_choice_v2"]])
    st.session_state.setdefault("input_mode", "Tự nhận dạng")

    with st.sidebar:
        st.header("Thiết lập biểu thức")
        st.selectbox("Ví dụ mẫu · 12 ca DT067", list(EXAMPLES), key="example_choice_v2", on_change=_load_example)
        st.caption("Có đủ 12 ca trong phiếu kiểm thử và 2 ví dụ giáo trình (kết quả 9, 15).")
        st.selectbox("Cách nhập", ["Tự nhận dạng", "Hậu tố", "Trung tố (tự chuyển)"], key="input_mode")
        input_label = "Biểu thức mới" if st.session_state["input_mode"] == "Tự nhận dạng" else ("Biểu thức hậu tố" if st.session_state["input_mode"] == "Hậu tố" else "Biểu thức toán học")
        input_help = ("Nhập tự do dạng 2+4*3 hoặc hậu tố 2 4 3 * +; web sẽ tự nhận dạng."
                      if st.session_state["input_mode"] == "Tự nhận dạng" else ("Ví dụ: 8 5 - 2 *. Nhập số và toán tử cách nhau bằng khoảng trắng."
                      if st.session_state["input_mode"] == "Hậu tố" else "Ví dụ: 8 - 5 * 2. Hỗ trợ ngoặc và + - * / ^."))
        expression = st.text_input(input_label, key="expression_input", help=input_help)
        st.caption("Mặc định tự nhận dạng hậu tố/trung tố. Toán hạng phải b được lấy trước khi chạy thuật toán stack.")
        st.divider()
        st.markdown("**Chạy trên máy của bạn**\n\n`pip install streamlit pandas`\n\n`streamlit run app.py`")

    st.markdown("""
    <section class="hero">
      <h1>Tính giá trị biểu thức hậu tố bằng ngăn xếp</h1>
      <p>Quan sát cách mỗi token thay đổi ngăn xếp và kiểm chứng phép tính theo quy tắc pop toán hạng phải trước.</p>
      <div class="identity"><span><strong>Đồ án</strong> INT13185 · DT067</span><span><strong>Sinh viên</strong> Nguyễn Thành Tân · N24DCDT082</span><span><strong>Lớp</strong> D24CQDT01-N · Nhóm 03</span><span><strong>Giáo trình</strong> Chương 5 · Mục 5.3.4.2 · Ví dụ 5.3</span></div>
    </section>
    """, unsafe_allow_html=True)

    tab_trace, tab_tests, tab_about = st.tabs(["Mô phỏng lần vết", "Bộ kiểm thử · 12 ca", "Quy tắc thuật toán"])
    with tab_trace:
        try:
            postfix_expression = normalize_expression(expression, st.session_state["input_mode"])
            if postfix_expression != expression:
                st.info(f"Đã nhận biểu thức trung tố và chuyển sang hậu tố: `{postfix_expression}`")
            result = evaluate_postfix_with_trace(postfix_expression)
            max_step = len(result["tokens"])
            st.session_state["execution_step_max"] = max_step
            st.session_state.setdefault("execution_step", 0)
            st.session_state["execution_step"] = min(max(0, st.session_state["execution_step"]), max_step)
            step = st.slider("Bước thực thi", min_value=0, max_value=max_step, step=1, key="execution_step",
                             help="Dùng nút bước trước/sau, phím mũi tên hoặc kéo thanh trượt.")
            previous_col, next_col, step_note = st.columns([1, 1, 3])
            with previous_col:
                st.button("← Bước trước", on_click=_move_step, args=(-1,), disabled=step == 0,
                          width="stretch", key="previous_step")
            with next_col:
                st.button("Bước tiếp →", on_click=_move_step, args=(1,), disabled=step == max_step,
                          width="stretch", key="next_step")
            with step_note:
                st.caption("Mỗi lần chuyển bước sẽ cập nhật token, stack và phép tính cùng lúc.")
            completed = step == len(result["tokens"])
            state_label = "Hoàn tất" if completed else "Đang mô phỏng"
            result_value = html.escape(str(result["value"])) if completed else "—"
            result_label = "Kết quả" if completed else "Kết quả cuối sẽ hiện khi hoàn tất"
            st.markdown(
                f'<div class="status-strip" aria-live="polite"><span class="status-result">{result_value}</span>'
                f'<span class="status-label">{result_label}</span><span class="status-chip">{state_label} · {step}/{len(result["tokens"])} token</span></div>',
                unsafe_allow_html=True,
            )

            st.markdown('<div class="content-heading">Dòng token</div><div class="content-subtitle">Đã xử lý · token hiện tại · các token tiếp theo</div>', unsafe_allow_html=True)
            token_html = []
            for i, token in enumerate(result["tokens"]):
                cls = "active" if i == step - 1 else "done" if i < step else ""
                operator = " operator" if token in {"+", "-", "*", "/", "^"} else ""
                token_html.append(f'<span class="token {cls}{operator}" aria-label="Token {i + 1}: {html.escape(token)}">{html.escape(token)}</span>')
            st.markdown('<div class="token-rail" role="list">' + "".join(token_html) + '</div>', unsafe_allow_html=True)
            stack_col, action_col = st.columns([1.1, 1], gap="large")
            with stack_col:
                current_stack = result["snapshots"][step]
                if current_stack:
                    cells = []
                    for index, value in enumerate(reversed(current_stack)):
                        pos = "ĐỈNH" if index == 0 else f"VỊ TRÍ {index + 1}"
                        top_class = " top" if index == 0 else ""
                        cells.append(f'<div class="stack-cell{top_class}" role="listitem"><span class="stack-pos">{pos}</span><span class="stack-val">{value}</span></div>')
                    stack_content = '<div class="stack-gauge"><span>TOP</span><span>BOTTOM</span></div><div class="stack-cells">' + "".join(cells) + '</div>'
                else:
                    stack_content = '<div class="stack-gauge"><span>TOP</span><span>BOTTOM</span></div><div class="empty-stack">Chưa có giá trị · stack rỗng</div>'
                st.markdown(f'<section class="panel"><div class="content-heading">Ngăn xếp</div><div class="content-subtitle">Sau bước {step} · phần tử trên cùng ở đầu</div><div class="stack-shell" role="list" aria-label="Các phần tử trong ngăn xếp">{stack_content}</div></section>', unsafe_allow_html=True)
            with action_col:
                if step:
                    row = result["trace"][step - 1]
                    operation_html = (f'<div class="op-card"><span class="op-badge">TOKEN {step} · {html.escape(str(row["Token"]))}</span>'
                                      f'<div class="calc">{html.escape(str(row["Phép tính"]))}</div><div class="hint">{html.escape(str(row["Thao tác"]))}</div>'
                                      f'<div class="hint">b (phải) = <strong>{html.escape(str(row["b (Phải)"]))}</strong> &nbsp; · &nbsp; a (trái) = <strong>{html.escape(str(row["a (Trái)"]))}</strong></div></div>')
                else:
                    operation_html = '<div class="op-card"><span class="op-badge">SẴN SÀNG</span><div class="calc">Bắt đầu với stack rỗng</div><div class="hint">Chọn “Bước tiếp” hoặc kéo thanh tiến độ để xử lý token đầu tiên.</div></div>'
                st.markdown(
                    '<section class="panel"><div class="content-heading">Diễn giải thao tác</div>'
                    '<div class="content-subtitle">Thứ tự lấy toán hạng theo quy tắc DT067</div>'
                    + operation_html
                    + '<div class="hint">Phép toán luôn tính theo thứ tự <strong>a op b</strong>. Với phép chia, kết quả được cắt về 0 như C++/Julia.</div></section>',
                    unsafe_allow_html=True,
                )

            st.markdown('<div style="height:1.25rem"></div><div class="content-heading">Bảng lần vết</div><div class="content-subtitle">Bảng đầy đủ để đối chiếu và đưa vào báo cáo.</div>', unsafe_allow_html=True)
            trace_df = pd.DataFrame(result["trace"], columns=TRACE_COLUMNS)
            # Keep mixed number/text fields consistent for Streamlit's Arrow table renderer.
            trace_df[["b (Phải)", "a (Trái)"]] = trace_df[["b (Phải)", "a (Trái)"]].astype(str)
            st.dataframe(trace_df, width="stretch", hide_index=True)
            download_csv, download_md, spacer = st.columns([1, 1, 4])
            with download_csv:
                st.download_button("Tải bảng CSV", trace_df.to_csv(index=False).encode("utf-8-sig"), file_name="lan_vet_hau_to.csv", mime="text/csv", width="stretch")
            markdown = "| " + " | ".join(TRACE_COLUMNS) + " |\n|" + "|".join(["---"] * len(TRACE_COLUMNS)) + "|\n"
            for _, row in trace_df.iterrows():
                markdown += "| " + " | ".join(str(row[col]).replace("|", "\\|") for col in TRACE_COLUMNS) + " |\n"
            with download_md:
                st.download_button("Tải bảng Markdown", markdown.encode("utf-8"), file_name="lan_vet_hau_to.md", mime="text/markdown", width="stretch")
        except (ValueError, ZeroDivisionError, OverflowError) as exc:
            if "dư toán hạng" in str(exc):
                st.warning("Chưa thể tính vì biểu thức có các số chưa được nối bằng toán tử. "
                           "Ví dụ trung tố: `2 + 4 * 3`; ví dụ hậu tố: `2 4 3 * +`.")
            else:
                st.error(str(exc))
                st.caption("Web vẫn hoạt động; kiểm tra toán tử và dấu ngoặc. Ví dụ `2 + 4 * 3` cho kết quả 14.")

    with tab_tests:
        st.header("Bộ kiểm thử DT067")
        st.caption("12 ca bao gồm ví dụ giáo trình, phép trừ thứ tự, chia số âm, số mũ và tình huống lỗi.")
        tests_df = run_test_suite()
        tests_df[["Expected", "Actual"]] = tests_df[["Expected", "Actual"]].astype(str)
        passed_count = int((tests_df["Trạng thái"] == "PASS").sum())
        total_cols = st.columns([1, 1, 3])
        total_cols[0].metric("Ca đạt", f"{passed_count}/{len(tests_df)}")
        total_cols[1].metric("Ca lỗi", len(tests_df) - passed_count)
        total_cols[2].markdown('<div class="hint" style="padding-top:14px">Màu trạng thái luôn đi kèm nhãn PASS/FAIL để dễ đọc và không phụ thuộc riêng vào màu sắc.</div>', unsafe_allow_html=True)
        st.dataframe(tests_df, width="stretch", hide_index=True)
        st.download_button("Tải kết quả kiểm thử CSV", tests_df.to_csv(index=False).encode("utf-8-sig"), file_name="ket_qua_kiem_thu_DT067.csv", mime="text/csv")

    with tab_about:
        st.header("Quy tắc tính hậu tố")
        st.markdown("""
        <div class="panel">
          <div class="panel-title">Một lượt xử lý toán tử</div>
          <div class="panel-subtitle">Lấy hai giá trị trên đỉnh stack theo thứ tự đề tài yêu cầu.</div>
          <div class="op-card"><span class="op-badge">1 · POP b</span><div class="hint">Phần tử đầu tiên lấy khỏi stack là toán hạng <strong>phải</strong>.</div></div>
          <div style="height:10px"></div><div class="op-card"><span class="op-badge">2 · POP a</span><div class="hint">Phần tử tiếp theo là toán hạng <strong>trái</strong>.</div></div>
          <div style="height:10px"></div><div class="op-card"><span class="op-badge">3 · TÍNH a op b</span><div class="hint">Đẩy kết quả trở lại stack; khi kết thúc phải còn đúng một giá trị.</div></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("- **Chia nguyên:** phép chia số nguyên cắt về 0, không chuyển qua số thực; `-7 / 2 = -3`.\n- **Lũy thừa:** `^` kết hợp phải; `2 3 2 ^ ^` tương ứng `2 ^ (3 ^ 2) = 512`.\n- **Nhập trung tố:** ứng dụng tự chuyển biểu thức toán học có ngoặc sang hậu tố trước khi chạy cùng thuật toán stack.\n- **Validator:** phát hiện token không hợp lệ, thiếu/dư toán hạng, chia cho 0 và tràn.")

if __name__ == "__main__":
    main()
