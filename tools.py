from __future__ import annotations

import re
import unicodedata
from collections import OrderedDict
from typing import Any

from langchain_core.tools import tool


FLIGHTS_DB = {
    ("Hà Nội", "Đà Nẵng"): [
        {"airline": "Vietnam Airlines", "departure": "06:00", "arrival": "07:20", "price": 1450000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "14:00", "arrival": "15:20", "price": 2800000, "class": "business"},
        {"airline": "VietJet Air", "departure": "08:30", "arrival": "09:50", "price": 890000, "class": "economy"},
        {"airline": "Bamboo Airways", "departure": "11:00", "arrival": "12:20", "price": 1200000, "class": "economy"},
    ],
    ("Hà Nội", "Phú Quốc"): [
        {"airline": "Vietnam Airlines", "departure": "07:00", "arrival": "09:15", "price": 2100000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "10:00", "arrival": "12:15", "price": 1350000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "16:00", "arrival": "18:15", "price": 1100000, "class": "economy"},
    ],
    ("Hà Nội", "Hồ Chí Minh"): [
        {"airline": "Vietnam Airlines", "departure": "06:00", "arrival": "08:10", "price": 1600000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "07:30", "arrival": "09:40", "price": 950000, "class": "economy"},
        {"airline": "Bamboo Airways", "departure": "12:00", "arrival": "14:10", "price": 1300000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "18:00", "arrival": "20:10", "price": 3200000, "class": "business"},
    ],
    ("Hồ Chí Minh", "Đà Nẵng"): [
        {"airline": "Vietnam Airlines", "departure": "09:00", "arrival": "10:20", "price": 1300000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "13:00", "arrival": "14:20", "price": 780000, "class": "economy"},
    ],
    ("Hồ Chí Minh", "Phú Quốc"): [
        {"airline": "Vietnam Airlines", "departure": "08:00", "arrival": "09:00", "price": 1100000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "15:00", "arrival": "16:00", "price": 650000, "class": "economy"},
    ],
}

HOTELS_DB = {
    "Đà Nẵng": [
        {"name": "Mường Thanh Luxury", "stars": 5, "price_per_night": 1800000, "area": "Mỹ Khê", "rating": 4.5},
        {"name": "Sala Danang Beach", "stars": 4, "price_per_night": 1200000, "area": "Mỹ Khê", "rating": 4.3},
        {"name": "Fivitel Danang", "stars": 3, "price_per_night": 650000, "area": "Sơn Trà", "rating": 4.1},
        {"name": "Memory Hostel", "stars": 2, "price_per_night": 250000, "area": "Hải Châu", "rating": 4.6},
        {"name": "Christina's Homestay", "stars": 2, "price_per_night": 350000, "area": "An Thượng", "rating": 4.7},
    ],
    "Phú Quốc": [
        {"name": "Vinpearl Resort", "stars": 5, "price_per_night": 3500000, "area": "Bãi Dài", "rating": 4.4},
        {"name": "Sol by Melia", "stars": 4, "price_per_night": 1500000, "area": "Bãi Trường", "rating": 4.2},
        {"name": "Lahana Resort", "stars": 3, "price_per_night": 800000, "area": "Dương Đông", "rating": 4.0},
        {"name": "9Station Hostel", "stars": 2, "price_per_night": 200000, "area": "Dương Đông", "rating": 4.5},
    ],
    "Hồ Chí Minh": [
        {"name": "Rex Hotel", "stars": 5, "price_per_night": 2800000, "area": "Quận 1", "rating": 4.3},
        {"name": "Liberty Central", "stars": 4, "price_per_night": 1400000, "area": "Quận 1", "rating": 4.1},
        {"name": "Cochin Zen Hotel", "stars": 3, "price_per_night": 550000, "area": "Quận 3", "rating": 4.4},
        {"name": "The Common Room", "stars": 2, "price_per_night": 180000, "area": "Quận 1", "rating": 4.6},
    ],
}

CITY_ALIASES = {
    "ha noi": "Hà Nội",
    "hn": "Hà Nội",
    "da nang": "Đà Nẵng",
    "dn": "Đà Nẵng",
    "phu quoc": "Phú Quốc",
    "pq": "Phú Quốc",
    "ho chi minh": "Hồ Chí Minh",
    "hcm": "Hồ Chí Minh",
    "hcmc": "Hồ Chí Minh",
    "sai gon": "Hồ Chí Minh",
    "saigon": "Hồ Chí Minh",
    "tp hcm": "Hồ Chí Minh",
    "tp ho chi minh": "Hồ Chí Minh",
}


def format_currency(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def prettify_expense_name(raw_name: str) -> str:
    cleaned = raw_name.strip().replace("_", " ")
    if not cleaned:
        return "Chi phí khác"
    return cleaned[:1].upper() + cleaned[1:]


def _clean_whitespace(value: str) -> str:
    return " ".join(value.strip().split())


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    return "".join(character for character in normalized if unicodedata.category(character) != "Mn")


def _normalize_city_key(value: str) -> str:
    cleaned = _clean_whitespace(value).casefold()
    return _strip_accents(cleaned)


def _build_city_lookup() -> dict[str, str]:
    cities: set[str] = set(HOTELS_DB)
    for origin, destination in FLIGHTS_DB:
        cities.add(origin)
        cities.add(destination)

    lookup = {_normalize_city_key(city): city for city in cities}
    for alias, canonical in CITY_ALIASES.items():
        lookup[_normalize_city_key(alias)] = canonical
    return lookup


CITY_LOOKUP = _build_city_lookup()


def canonicalize_city(raw_city: str) -> str:
    cleaned = _clean_whitespace(raw_city)
    if not cleaned:
        return ""
    return CITY_LOOKUP.get(_normalize_city_key(cleaned), cleaned)


def parse_amount_text(amount_text: str) -> int | None:
    sanitized = amount_text.strip()
    if not sanitized:
        return None

    number_tokens = re.findall(r"\d[\d\.,]*", sanitized)
    if not number_tokens:
        return None

    normalized_numbers = [int(re.sub(r"[^\d]", "", token)) for token in number_tokens]
    multiplication_present = bool(re.search(r"[×*]|\bx\b", sanitized, flags=re.IGNORECASE))

    if len(normalized_numbers) == 1:
        return normalized_numbers[0]
    if multiplication_present:
        total = 1
        for number in normalized_numbers:
            total *= number
        return total
    return None


def _format_flight_lines(flights: list[dict[str, Any]], origin: str, destination: str) -> str:
    sorted_flights = sorted(flights, key=lambda item: int(item["price"]))
    lines = [f"Danh sách chuyến bay từ {origin} đến {destination}:"]
    for index, flight in enumerate(sorted_flights, start=1):
        lines.append(
            (
                f"{index}. {flight['airline']} | {flight['departure']} - {flight['arrival']} | "
                f"Hạng {flight['class']} | {format_currency(int(flight['price']))} VND"
            )
        )
    return "\n".join(lines)


def _format_hotel_lines(hotels: list[dict[str, Any]], city: str, max_price_per_night: int) -> str:
    lines = [
        f"Khách sạn phù hợp tại {city} (tối đa {format_currency(max_price_per_night)} VND/đêm):"
    ]
    for index, hotel in enumerate(hotels, start=1):
        lines.append(
            (
                f"{index}. {hotel['name']} | {hotel['stars']} sao | "
                f"{format_currency(int(hotel['price_per_night']))} VND/đêm | "
                f"Khu vực: {hotel['area']} | Rating: {hotel['rating']}"
            )
        )
    return "\n".join(lines)


def _coerce_positive_budget(value: int, field_name: str) -> int:
    normalized_value = int(value)
    if normalized_value < 0:
        raise ValueError(f"{field_name} phải là số không âm.")
    return normalized_value


def _parse_expense_item(item: str) -> tuple[str, int] | None:
    if "=" in item:
        name, amount_text = item.split("=", 1)
    elif ":" in item:
        name, amount_text = item.split(":", 1)
    else:
        return None

    parsed_name = name.strip()
    parsed_amount = parse_amount_text(amount_text)
    if not parsed_name or parsed_amount is None:
        return None
    return parsed_name, parsed_amount


@tool
def search_flights(origin: str, destination: str) -> str:
    """
    Tìm kiếm các chuyến bay giữa hai thành phố.
    """
    try:
        origin = canonicalize_city(origin)
        destination = canonicalize_city(destination)

        if not origin or not destination:
            return "Thiếu thông tin điểm đi hoặc điểm đến. Vui lòng nhập đầy đủ tên thành phố."
        if origin == destination:
            return "Điểm đi và điểm đến đang trùng nhau. Vui lòng kiểm tra lại hành trình."

        direct_key = (origin, destination)
        reverse_key = (destination, origin)

        if direct_key in FLIGHTS_DB:
            return _format_flight_lines(FLIGHTS_DB[direct_key], origin, destination)

        if reverse_key in FLIGHTS_DB:
            reverse_lines = _format_flight_lines(FLIGHTS_DB[reverse_key], destination, origin)
            return (
                f"Hiện chưa có dữ liệu chuyến bay chiều {origin} -> {destination}.\n"
                f"Tuy nhiên tôi tìm thấy chiều ngược lại để bạn tham khảo:\n{reverse_lines}"
            )

        return f"Không tìm thấy chuyến bay từ {origin} đến {destination}."
    except Exception as exc:
        return f"Lỗi khi tìm chuyến bay: {exc}"


@tool
def search_hotels(city: str, max_price_per_night: int = 99_999_999) -> str:
    """
    Tìm kiếm khách sạn tại một thành phố, có thể lọc theo giá tối đa mỗi đêm.
    """
    try:
        city = canonicalize_city(city)
        budget_limit = _coerce_positive_budget(max_price_per_night, "Giá tối đa mỗi đêm")

        if not city:
            return "Thiếu tên thành phố để tìm khách sạn."

        hotels = HOTELS_DB.get(city)
        if not hotels:
            return f"Không có dữ liệu khách sạn cho thành phố {city}."

        filtered_hotels = [
            hotel for hotel in hotels if int(hotel["price_per_night"]) <= budget_limit
        ]
        filtered_hotels.sort(
            key=lambda hotel: (-float(hotel["rating"]), int(hotel["price_per_night"]))
        )

        if not filtered_hotels:
            return (
                f"Không tìm thấy khách sạn tại {city} với giá dưới "
                f"{format_currency(budget_limit)} VND/đêm. Hãy thử tăng ngân sách."
            )

        return _format_hotel_lines(filtered_hotels, city, budget_limit)
    except Exception as exc:
        return f"Lỗi khi tìm khách sạn: {exc}"


@tool
def calculate_budget(total_budget: int, expenses: str) -> str:
    """
    Tính toán ngân sách còn lại sau khi trừ các khoản chi phí.
    """
    try:
        available_budget = _coerce_positive_budget(total_budget, "Ngân sách tổng")

        normalized_expenses = expenses.replace("+", ",")
        raw_items = [_clean_whitespace(item) for item in normalized_expenses.split(",") if item.strip()]
        if not raw_items:
            return "Chuỗi expenses đang trống. Vui lòng dùng định dạng tên_khoản=số_tiền."

        parsed_expenses: OrderedDict[str, int] = OrderedDict()
        for item in raw_items:
            parsed_item = _parse_expense_item(item)
            if parsed_item is None:
                return (
                    "Định dạng expenses không hợp lệ. "
                    "Vui lòng dùng dạng tên_khoản=số_tiền, ví dụ: vé_máy_bay=890000."
                )

            name, amount = parsed_item
            parsed_expenses[name] = parsed_expenses.get(name, 0) + amount

        total_expense = sum(parsed_expenses.values())
        remaining = available_budget - total_expense

        lines = ["Bảng chi phí:"]
        for name, amount in parsed_expenses.items():
            lines.append(f"- {prettify_expense_name(name)}: {format_currency(amount)} VND")

        lines.append("")
        lines.append(f"Tổng chi: {format_currency(total_expense)} VND")
        lines.append(f"Ngân sách: {format_currency(available_budget)} VND")

        if remaining >= 0:
            lines.append(f"Còn lại: {format_currency(remaining)} VND")
        else:
            lines.append(f"Còn lại: -{format_currency(abs(remaining))} VND")
            lines.append(f"Vượt ngân sách {format_currency(abs(remaining))} đồng! Cần điều chỉnh.")

        return "\n".join(lines)
    except Exception as exc:
        return f"Lỗi khi tính ngân sách: {exc}"
