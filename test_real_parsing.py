#!/usr/bin/env python3
"""
Test script for data parsing functionality using the actual DataInputPopup class
"""

import sys
import os

# Add the current directory to the path so we can import from scoshow_remote_super
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scoshow_remote_super import DataInputPopup

def test_tab_separated_data():
    """Test tab-separated data parsing"""
    print("=" * 60)
    print("Testing Tab-separated data:")
    print("=" * 60)
    
    # Tab-separated data
    test_data = """Round 1\t60050
Round 1\t555
Round 1\t60111
Round 1\t1002431
Round 1\t1012353
Round 1\t60192
Round 1\t60238
Round 1\t1006268
Round 1\t60141
Round 1\t83410"""
    
    popup = DataInputPopup()
    result = popup.parse_data(test_data)
    
    print(f"\nParsed {len(result)} rows:")
    for row in result:
        print(f"  {row['rank']}: Member {row['member_id']} (Round {row['round']})")
    
    return result

def test_space_separated_data():
    """Test space-separated data parsing"""
    print("=" * 60)
    print("Testing Space-separated data:")
    print("=" * 60)
    
    # Space-separated data (multiple spaces)
    test_data = """Round 1    60050
Round 1    555
Round 1    60111
Round 1    1002431
Round 1    1012353"""
    
    popup = DataInputPopup()
    result = popup.parse_data(test_data)
    
    print(f"\nParsed {len(result)} rows:")
    for row in result:
        print(f"  {row['rank']}: Member {row['member_id']} (Round {row['round']})")
    
    return result

def test_line_by_line_data():
    """Test the exact data format from the screenshot"""
    print("=" * 60)
    print("Testing Line-by-line data (from screenshot):")
    print("=" * 60)
    
    # This is the exact format from the screenshot - alternating lines
    test_data = """Round 1
60050
Round 1
555
Round 1
60111
Round 1
1002431
Round 1
1012353"""
    
    popup = DataInputPopup()
    result = popup.parse_data(test_data)
    
    print(f"\nParsed {len(result)} rows:")
    for row in result:
        print(f"  {row['rank']}: Member {row['member_id']} (Round {row['round']})")
    
    return result

def test_data_with_headers():
    """Test data with header row"""
    print("=" * 60)
    print("Testing Data with headers:")
    print("=" * 60)
    
    # Data with headers (should skip the header row)
    test_data = """Round\tMB\tNAME\tCredit\tLast Bet
Round 1\t60050\tHO CUONG DIEU\t30900
Round 1\t555\tCHWEE WAI ONN\t21180
Round 1\t60111\tNGUYEN VAN A\t15000"""
    
    popup = DataInputPopup()
    result = popup.parse_data(test_data)
    
    print(f"\nParsed {len(result)} rows:")
    for row in result:
        print(f"  {row['rank']}: Member {row['member_id']} (Round {row['round']})")
    
    return result

if __name__ == "__main__":
    test_tab_separated_data()
    test_space_separated_data()
    test_line_by_line_data()
    test_data_with_headers()
