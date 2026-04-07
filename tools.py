from __future__ import annotations

import re
from typing import Dict, List

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


def format_currency(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def prettify_expense_name(raw_name: str) -> str:
    cleaned = raw_name.strip().replace("_", " ")
    if not cleaned:
        return "Chi phí khác"
    return cleaned[:1].upper() + cleaned[1:]


def parse_amount_text(amount_text: str) -> int | None:
    amount_text = amount_text.split("=", 1)[0]
    number_tokens = re.findall(r"\d[\d\.]*", amount_text)
    if not number_tokens:
        return None

    normalized_numbers = [int(token.replace(".", "")) for token in number_tokens]
    if any(operator in amount_text.lower() for operator in ("*", " x ", "×")) and len(normalized_numbers) >= 2:
        total = 1
        for number in normalized_numbers:
            total *= number
        return total
    return normalized_numbers[0]


def _format_flight_lines(flights: List[Dict[str, object]], origin: str, destination: str) -> str:
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


@tool
def search_flights(origin: str, destination: str) -> str:
    """
    Tìm kiếm các chuyến bay giữa hai thành phố.
    """
    try:
        origin = origin.strip()
        destination = destination.strip()
        if not origin or not destination:
            return "Thiếu thông tin điểm đi hoặc điểm đến. Vui lòng nhập đầy đủ tên thành phố."

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
        city = city.strip()
        if not city:
            return "Thiếu tên thành phố để tìm khách sạn."

        hotels = HOTELS_DB.get(city)
        if not hotels:
            return f"Không có dữ liệu khách sạn cho thành phố {city}."

        filtered_hotels = [
            hotel for hotel in hotels if int(hotel["price_per_night"]) <= int(max_price_per_night)
        ]
        filtered_hotels.sort(
            key=lambda hotel: (-float(hotel["rating"]), int(hotel["price_per_night"]))
        )

        if not filtered_hotels:
            return (
                f"Không tìm thấy khách sạn tại {city} với giá dưới "
                f"{format_currency(int(max_price_per_night))} VND/đêm. Hãy thử tăng ngân sách."
            )

        lines = [
            f"Khách sạn phù hợp tại {city} (tối đa {format_currency(int(max_price_per_night))} VND/đêm):"
        ]
        for index, hotel in enumerate(filtered_hotels, start=1):
            lines.append(
                (
                    f"{index}. {hotel['name']} | {hotel['stars']} sao | "
                    f"{format_currency(int(hotel['price_per_night']))} VND/đêm | "
                    f"Khu vực: {hotel['area']} | Rating: {hotel['rating']}"
                )
            )
        return "\n".join(lines)
    except Exception as exc:
        return f"Lỗi khi tìm khách sạn: {exc}"


@tool
def calculate_budget(total_budget: int, expenses: str) -> str:
    """
    Tính toán ngân sách còn lại sau khi trừ các khoản chi phí.
    """
    try:
        if int(total_budget) < 0:
            return "Ngân sách tổng phải là số không âm."

        normalized_expenses = expenses.replace("+", ",")
        raw_items = [item.strip() for item in normalized_expenses.split(",") if item.strip()]
        if not raw_items:
            return "Chuỗi expenses đang trống. Vui lòng dùng định dạng tên_khoản=số_tiền."

        parsed_expenses: Dict[str, int] = {}
        for item in raw_items:
            name = ""
            amount_text = ""
            if "=" in item:
                name, amount_text = item.split("=", 1)
            elif ":" in item:
                name, amount_text = item.split(":", 1)
            else:
                return (
                    "Định dạng expenses không hợp lệ. "
                    "Vui lòng dùng dạng tên_khoản=số_tiền, ví dụ: vé_máy_bay=890000."
                )

            name = name.strip()
            parsed_amount = parse_amount_text(amount_text)
            if not name or parsed_amount is None:
                return "Mỗi khoản chi phải có đủ tên và số tiền."
            parsed_expenses[name] = parsed_expenses.get(name, 0) + parsed_amount

        total_expense = sum(parsed_expenses.values())
        remaining = int(total_budget) - total_expense

        lines = ["Bảng chi phí:"]
        for name, amount in parsed_expenses.items():
            lines.append(f"- {prettify_expense_name(name)}: {format_currency(amount)} VND")

        lines.append("")
        lines.append(f"Tổng chi: {format_currency(total_expense)} VND")
        lines.append(f"Ngân sách: {format_currency(int(total_budget))} VND")

        if remaining >= 0:
            lines.append(f"Còn lại: {format_currency(remaining)} VND")
        else:
            lines.append(f"Còn lại: -{format_currency(abs(remaining))} VND")
            lines.append(f"Vượt ngân sách {format_currency(abs(remaining))} đồng! Cần điều chỉnh.")

        return "\n".join(lines)
    except Exception as exc:
        return f"Lỗi khi tính ngân sách: {exc}"
