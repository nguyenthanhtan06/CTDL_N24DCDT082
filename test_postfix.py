"""Kiểm thử độc lập bộ đánh giá hậu tố DT067."""
import unittest

from app import TEST_CASES, evaluate_postfix_with_trace, infix_to_postfix, normalize_expression


class PostfixEvaluationTests(unittest.TestCase):
    def test_12_cases_required_by_report(self):
        for case_id, expression, expected in TEST_CASES:
            with self.subTest(case_id=case_id, expression=expression):
                if isinstance(expected, int):
                    self.assertEqual(evaluate_postfix_with_trace(expression)["value"], expected)
                elif expected == "Lỗi chia cho 0":
                    with self.assertRaises(ZeroDivisionError):
                        evaluate_postfix_with_trace(expression)
                elif expected == "Lỗi tràn Int128":
                    with self.assertRaises(OverflowError):
                        evaluate_postfix_with_trace(expression)
                else:
                    with self.assertRaises(ValueError):
                        evaluate_postfix_with_trace(expression)

    def test_optional_negative_input_division_cuts_toward_zero(self):
        self.assertEqual(evaluate_postfix_with_trace("-7 2 /")["value"], -3)

    def test_division_uses_exact_integer_arithmetic(self):
        expression = "100 10 ^ 2 * 3 /"
        self.assertEqual(evaluate_postfix_with_trace(expression)["value"], 66666666666666666666)

    def test_infix_mode_converts_arbitrary_valid_expression(self):
        postfix = infix_to_postfix("2 + 4 * 3")
        self.assertEqual(postfix, "2 4 3 * +")
        self.assertEqual(evaluate_postfix_with_trace(postfix)["value"], 14)
        self.assertEqual(infix_to_postfix("2 ^ 3 ^ 2"), "2 3 2 ^ ^")

    def test_auto_mode_accepts_infix_and_postfix_inputs(self):
        infix = normalize_expression("(8 - 5) * 2")
        postfix = normalize_expression("8 5 - 2 *")
        self.assertEqual(evaluate_postfix_with_trace(infix)["value"], 6)
        self.assertEqual(evaluate_postfix_with_trace(postfix)["value"], 6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
