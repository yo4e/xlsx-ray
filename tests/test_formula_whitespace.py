from xlsx_ray.formulas import normalize_formula


def test_formula_normalization_preserves_leading_and_trailing_whitespace() -> None:
    assert normalize_formula("  =sum(A1)  ") == "  =SUM(A1)  "
    assert normalize_formula("   ") == "   "
