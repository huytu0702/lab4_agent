from tools import calculate_budget, canonicalize_city, parse_amount_text, search_flights, search_hotels


def test_canonicalize_city_supports_common_aliases() -> None:
    assert canonicalize_city("ha noi") == "Hà Nội"
    assert canonicalize_city("Sài Gòn") == "Hồ Chí Minh"
    assert canonicalize_city("  đà   nẵng ") == "Đà Nẵng"


def test_parse_amount_text_supports_multiplication_patterns() -> None:
    assert parse_amount_text("1.500.000 x 2 đêm") == 3_000_000
    assert parse_amount_text("1500000*2") == 3_000_000
    assert parse_amount_text("1.500.000 VND × 2") == 3_000_000


def test_parse_amount_text_rejects_ambiguous_multiple_numbers() -> None:
    assert parse_amount_text("1.500.000 2 đêm") is None


def test_search_flights_returns_sorted_results() -> None:
    response = search_flights.invoke({"origin": "Hà Nội", "destination": "Đà Nẵng"})

    assert "Danh sách chuyến bay từ Hà Nội đến Đà Nẵng" in response
    assert "1. VietJet Air" in response
    assert "890.000 VND" in response


def test_search_hotels_applies_budget_and_sorting() -> None:
    response = search_hotels.invoke({"city": "Phú Quốc", "max_price_per_night": 1_000_000})

    assert "Khách sạn phù hợp tại Phú Quốc" in response
    assert "9Station Hostel" in response
    assert "Vinpearl Resort" not in response


def test_calculate_budget_supports_duplicate_expenses_and_remaining_budget() -> None:
    response = calculate_budget.invoke(
        {
            "total_budget": 5_000_000,
            "expenses": "vé_máy_bay=1.100.000,khách_sạn=1.500.000 x 2,ăn_uống=400000,ăn_uống=100000",
        }
    )

    assert "Vé máy bay: 1.100.000 VND" in response
    assert "Khách sạn: 3.000.000 VND" in response
    assert "Ăn uống: 500.000 VND" in response
    assert "Còn lại: 400.000 VND" in response


def test_calculate_budget_reports_invalid_format() -> None:
    response = calculate_budget.invoke({"total_budget": 5_000_000, "expenses": "vé máy bay 900000"})

    assert "Định dạng expenses không hợp lệ" in response
