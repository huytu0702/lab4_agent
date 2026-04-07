# Test Results

Kết quả chạy thực tế bằng `venv` và API key trong `.env`.

## Test 1 - Direct Answer

**User:**
Xin chào! Tôi đang muốn đi du lịch nhưng chưa biết đi đâu.

**Console log:**
```text
[Trả lời trực tiếp]
```

**TravelBuddy:**
Chào bạn! Để giúp bạn lên kế hoạch cho chuyến đi, bạn có thể cho tôi biết điểm đến mong muốn, thời gian đi và ngân sách dự kiến của bạn không?

---

## Test 2 - Single Tool Call

**User:**
Tìm giúp tôi chuyến bay từ Hà Nội đi Đà Nẵng

**Console log:**
```text
[Gọi tool: search_flights]({'origin': 'Hà Nội', 'destination': 'Đà Nẵng'})
[Trả lời trực tiếp]
```

**TravelBuddy:**
Dưới đây là danh sách chuyến bay từ Hà Nội đi Đà Nẵng:

1. **VietJet Air**: 08:30 - 09:50 | Hạng economy | 890.000 VND
2. **Bamboo Airways**: 11:00 - 12:20 | Hạng economy | 1.200.000 VND
3. **Vietnam Airlines**: 06:00 - 07:20 | Hạng economy | 1.450.000 VND
4. **Vietnam Airlines**: 14:00 - 15:20 | Hạng business | 2.800.000 VND

Nếu bạn cần thêm thông tin về khách sạn hoặc lên kế hoạch cho chuyến đi, hãy cho tôi biết nhé!

---

## Test 3 - Multi-step Tool Chaining

**User:**
Tôi ở Hà Nội, muốn đi Phú Quốc 2 đêm, budget 5 triệu. Tư vấn giúp.

**Console log:**
```text
[Gọi tool: search_flights]({'origin': 'Hà Nội', 'destination': 'Phú Quốc'})
[Gọi tool: search_hotels]({'city': 'Phú Quốc', 'max_price_per_night': 2500000})
[Gọi tool: calculate_budget]({'total_budget': 5000000, 'expenses': 'Chuyến bay: 1.100.000 VND + Khách sạn: 2 đêm x 1.500.000 VND'})
[Trả lời trực tiếp]
```

**TravelBuddy:**
Dưới đây là gợi ý cho chuyến đi của bạn từ Hà Nội đến Phú Quốc trong 2 đêm với ngân sách 5 triệu:

**Chuyến bay:**
- VietJet Air | 16:00 - 18:15 | Hạng economy | 1.100.000 VND

**Khách sạn:**
- Sol by Melia | 4 sao | 1.500.000 VND/đêm | Tổng chi phí cho 2 đêm: 3.000.000 VND

**Tổng chi phí ước tính:**
- Chuyến bay: 1.100.000 VND
- Khách sạn: 3.000.000 VND
- **Tổng chi: 4.100.000 VND**
- **Ngân sách còn lại: 900.000 VND**

Gợi ý thêm: Bạn có thể sử dụng số tiền còn lại để thưởng thức ẩm thực địa phương hoặc tham gia các hoạt động vui chơi tại Phú Quốc. Nếu cần thêm thông tin hoặc hỗ trợ gì khác, hãy cho mình biết nhé!

---

## Test 4 - Missing Info / Clarification

**User:**
Tôi muốn đặt khách sạn

**Console log:**
```text
[Trả lời trực tiếp]
```

**TravelBuddy:**
Bạn có thể cho mình biết bạn muốn đặt khách sạn ở thành phố nào và ngân sách tối đa mỗi đêm là bao nhiêu không?

---

## Test 5 - Guardrail / Refusal

**User:**
Giải giúp tôi bài tập lập trình Python về linked list

**Console log:**
```text
[Trả lời trực tiếp]
```

**TravelBuddy:**
Xin lỗi, nhưng tôi chỉ có thể hỗ trợ các yêu cầu liên quan đến du lịch, chuyến bay, khách sạn và ngân sách chuyến đi. Nếu bạn cần tư vấn về du lịch, hãy cho tôi biết điểm đến, thời gian đi và ngân sách dự kiến của bạn nhé!

---
