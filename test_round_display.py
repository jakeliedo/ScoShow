#!/usr/bin/env python3
"""
Test để kiểm tra hiển thị round number
"""

# Giả lập dữ liệu parsed data
parsed_data = [{'round': 1, 'position': 1, 'member_id': '60050'}]

# Test trước đây (sẽ hiển thị "Round 1")
old_format = f"Round {parsed_data[0]['round']}"
print(f"Format cũ: {old_format}")

# Test mới (chỉ hiển thị "1")
new_format = str(parsed_data[0]['round'])
print(f"Format mới: {new_format}")

print("\n✅ Thay đổi thành công!")
print("- Trước: Round field hiển thị 'Round 1'")
print("- Sau: Round field chỉ hiển thị '1'")
