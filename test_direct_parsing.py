#!/usr/bin/env python3
"""
Test script for data parsing functionality - direct method testing
"""

import sys
import os
import re

# Add the current directory to the path so we can import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_print(message):
    """Debug print function"""
    print(message)

# Copy the exact parse_data method from scoshow_remote_super.py
def parse_data(raw_data):
    """Parse the raw data into structured format with Round X validation"""
    debug_print(f"🔍 Starting to parse raw data:")
    debug_print(f"Raw data length: {len(raw_data)} characters")
    debug_print(f"Raw data preview: {raw_data[:200]}...")
    
    rows = raw_data.split('\n')
    parsed_data = []
    
    # Filter out empty rows and clean data
    clean_rows = []
    for row in rows:
        row_stripped = row.strip()
        if row_stripped:
            clean_rows.append(row_stripped)
    
    debug_print(f"🔍 Found {len(clean_rows)} non-empty rows")
    for i, row in enumerate(clean_rows[:10]):  # Show first 10
        debug_print(f"   Row {i+1}: '{row}'")
    
    if not clean_rows:
        debug_print("❌ No data rows found after filtering")
        return parsed_data
    
    # Format detection
    columnar_format = False
    line_by_line_format = False
    
    # Check for columnar format - look for rows that have "Round X" and a number on the same line
    for row in clean_rows[:5]:  # Check first 5 rows
        if '\t' in row or ('round' in row.lower() and len(row.split()) >= 2):
            # Check if it looks like "Round 1 60050" or "Round 1\t60050"
            parts = row.split('\t') if '\t' in row else row.split()
            if len(parts) >= 2:
                # For 3+ parts like "Round 1 60050", check if first two parts form "Round X"
                if len(parts) >= 3:
                    round_part = f"{parts[0]} {parts[1]}"  # "Round 1"
                    number_part = parts[2]  # The member ID
                else:
                    round_part = parts[0]  # "Round1" or similar
                    number_part = parts[1]  # The member ID
                
                if (re.search(r'round\s*\d+', round_part.lower()) and 
                    number_part.isdigit() and len(number_part) > 2):  # Member IDs are usually longer
                    columnar_format = True
                    break
    
    # Check for line-by-line format - alternating "Round X" and number lines
    if not columnar_format and len(clean_rows) >= 2:
        consecutive_round_lines = 0
        
        for i in range(0, min(len(clean_rows), 10), 2):  # Check pairs
            if i + 1 < len(clean_rows):
                line1 = clean_rows[i].strip()
                line2 = clean_rows[i + 1].strip()
                
                # Check if line1 is "Round X" and line2 is a number
                if (re.search(r'^round\s+\d+$', line1.lower()) and 
                    line2.isdigit() and len(line2) > 2):
                    consecutive_round_lines += 1
                else:
                    break
        
        # If we found at least 2 consecutive pairs, it's likely line-by-line format
        if consecutive_round_lines >= 2:
            line_by_line_format = True
    
    debug_print(f"🔍 Detected format: {'Columnar' if columnar_format else 'Line-by-line' if line_by_line_format else 'Auto-detect'}")
    
    round_number = None
    
    if line_by_line_format:
        debug_print("📋 Using LINE-BY-LINE parsing strategy")
        # Parse line-by-line format: alternating "Round X" and member number lines
        i = 0
        while i < len(clean_rows) - 1:
            row1 = clean_rows[i].strip()
            row2 = clean_rows[i + 1].strip()
            
            debug_print(f"🔍 Processing line-by-line pair {i//2 + 1}: '{row1}' + '{row2}'")
            
            # Check if first row is "Round X" format
            round_match = re.search(r'round\s+(\d+)', row1.lower())
            if round_match and row2.isdigit():
                current_round = int(round_match.group(1))
                member_value = row2
                
                debug_print(f"   Round info: '{row1}', Member value: '{member_value}'")
                debug_print(f"   Extracted round number: {current_round}")
                
                # Validate consistent round number
                if round_number is None:
                    round_number = current_round
                    debug_print(f"   Set round number to: {round_number}")
                elif round_number != current_round:
                    debug_print(f"❌ Inconsistent round number in pair {i//2 + 1}: found 'Round {current_round}', expected 'Round {round_number}'")
                    i += 2
                    continue
                
                # Position is based on order in the parsed data
                position = len(parsed_data) + 1
                
                data_row = {
                    'round': round_number,
                    'position': position,
                    'name': member_value,
                    'rank': f"{position}{'st' if position == 1 else 'nd' if position == 2 else 'rd' if position == 3 else 'th'}",
                    'member_id': member_value
                }
                parsed_data.append(data_row)
                debug_print(f"   ✅ Added data row: Position={position}, Round={round_number}, Member={member_value}")
                
                i += 2  # Move to next pair
            else:
                debug_print(f"❌ Invalid pair in lines {i+1}-{i+2}: '{row1}' + '{row2}' (expected 'Round X' + number)")
                i += 1  # Try next line
                
    elif columnar_format:
        debug_print("📋 Using COLUMNAR parsing strategy")
        # Parse columnar format: "Round 1\t60050" or "Round 1 60050"
        for row_index, row in enumerate(clean_rows):
            debug_print(f"🔍 Processing columnar row {row_index + 1}: '{row}'")
            
            # Try different separators: tab, multiple spaces, single space, comma
            columns = []
            if '\t' in row:
                columns = [col.strip() for col in row.split('\t') if col.strip()]
                debug_print(f"   Using tab separation: {columns}")
            elif '  ' in row:  # Multiple spaces
                columns = [col.strip() for col in row.split() if col.strip()]
                debug_print(f"   Using space separation: {columns}")
            elif ',' in row:
                columns = [col.strip() for col in row.split(',') if col.strip()]
                debug_print(f"   Using comma separation: {columns}")
            else:
                columns = [col.strip() for col in row.split() if col.strip()]
                debug_print(f"   Using default split: {columns}")
                
            if len(columns) >= 2:
                # Handle both "Round 1 60050" (3 parts) and "Round1 60050" (2 parts)
                if len(columns) >= 3 and columns[0].lower() == 'round' and columns[1].isdigit():
                    # Format: "Round 1 60050"
                    round_info = f"{columns[0]} {columns[1]}"
                    member_value = columns[2]
                elif len(columns) >= 2:
                    # Format: "Round1 60050" or any other 2-column format
                    round_info = columns[0]
                    member_value = columns[1]
                else:
                    debug_print(f"❌ Unexpected column format in row {row_index + 1}")
                    continue
                
                debug_print(f"   Round info: '{round_info}', Member value: '{member_value}'")
                
                # Extract and validate round number
                round_match = re.search(r'round\s*(\d+)', round_info.lower())
                if not round_match:
                    debug_print(f"❌ Invalid round format in row {row_index + 1}: '{round_info}' (expected 'Round X')")
                    continue
                
                current_round = int(round_match.group(1))
                debug_print(f"   Extracted round number: {current_round}")
                
                # Validate consistent round number
                if round_number is None:
                    round_number = current_round
                    debug_print(f"   Set round number to: {round_number}")
                elif round_number != current_round:
                    debug_print(f"❌ Inconsistent round number in row {row_index + 1}: found 'Round {current_round}', expected 'Round {round_number}'")
                    continue
                
                # Position is based on order in the parsed data
                position = len(parsed_data) + 1
                
                data_row = {
                    'round': round_number,
                    'position': position,
                    'name': member_value,
                    'rank': f"{position}{'st' if position == 1 else 'nd' if position == 2 else 'rd' if position == 3 else 'th'}",
                    'member_id': member_value
                }
                parsed_data.append(data_row)
                debug_print(f"   ✅ Added data row: Position={position}, Round={round_number}, Member={member_value}")
            else:
                debug_print(f"❌ Insufficient columns in row {row_index + 1}: {len(columns)} columns found, need at least 2")
    else:
        debug_print("📋 Using AUTO-DETECT parsing strategy")
        # Auto-detect and try both formats
        # Try columnar format first
        for row_index, row in enumerate(clean_rows):
            debug_print(f"🔍 Processing auto-detect row {row_index + 1}: '{row}'")
            
            # Try different separators: tab, multiple spaces, single space, comma
            columns = []
            if '\t' in row:
                columns = [col.strip() for col in row.split('\t') if col.strip()]
                debug_print(f"   Using tab separation: {columns}")
            elif '  ' in row:  # Multiple spaces
                columns = [col.strip() for col in row.split() if col.strip()]
                debug_print(f"   Using space separation: {columns}")
            elif ',' in row:
                columns = [col.strip() for col in row.split(',') if col.strip()]
                debug_print(f"   Using comma separation: {columns}")
            else:
                columns = [col.strip() for col in row.split() if col.strip()]
                debug_print(f"   Using default split: {columns}")
                
            if len(columns) >= 2:
                # Handle both "Round 1 60050" (3 parts) and "Round1 60050" (2 parts)
                if len(columns) >= 3 and columns[0].lower() == 'round' and columns[1].isdigit():
                    # Format: "Round 1 60050"
                    round_info = f"{columns[0]} {columns[1]}"
                    member_value = columns[2]
                elif len(columns) >= 2:
                    # Format: "Round1 60050" or any other 2-column format
                    round_info = columns[0]
                    member_value = columns[1]
                else:
                    debug_print(f"❌ Unexpected column format in row {row_index + 1}")
                    continue
                
                debug_print(f"   Round info: '{round_info}', Member value: '{member_value}'")
                
                # Extract and validate round number
                round_match = re.search(r'round\s*(\d+)', round_info.lower())
                if not round_match:
                    debug_print(f"❌ Invalid round format in row {row_index + 1}: '{round_info}' (expected 'Round X'), skipping")
                    continue
                
                current_round = int(round_match.group(1))
                debug_print(f"   Extracted round number: {current_round}")
                
                # Validate consistent round number
                if round_number is None:
                    round_number = current_round
                    debug_print(f"   Set round number to: {round_number}")
                elif round_number != current_round:
                    debug_print(f"❌ Inconsistent round number in row {row_index + 1}: found 'Round {current_round}', expected 'Round {round_number}'")
                    continue
                
                # Position is based on order in the parsed data
                position = len(parsed_data) + 1
                
                data_row = {
                    'round': round_number,
                    'position': position,
                    'name': member_value,
                    'rank': f"{position}{'st' if position == 1 else 'nd' if position == 2 else 'rd' if position == 3 else 'th'}",
                    'member_id': member_value
                }
                parsed_data.append(data_row)
                debug_print(f"   ✅ Added data row: Position={position}, Round={round_number}, Member={member_value}")
            else:
                debug_print(f"❌ Insufficient columns in row {row_index + 1}: {len(columns)} columns found, need at least 2")
                
    debug_print(f"✅ Successfully parsed {len(parsed_data)} rows for Round {round_number}")
    return parsed_data

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
    
    result = parse_data(test_data)
    
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
    
    result = parse_data(test_data)
    
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
    
    result = parse_data(test_data)
    
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
    
    result = parse_data(test_data)
    
    print(f"\nParsed {len(result)} rows:")
    for row in result:
        print(f"  {row['rank']}: Member {row['member_id']} (Round {row['round']})")
    
    return result

if __name__ == "__main__":
    test_tab_separated_data()
    test_space_separated_data()
    test_line_by_line_data()
    test_data_with_headers()
