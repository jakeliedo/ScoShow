#!/usr/bin/env python3
"""
Test script for data parsing functionality
"""

import re

def parse_data(raw_data):
    """Parse the raw data into structured format with Round X validation"""
    print(f"🔍 Starting to parse raw data:")
    print(f"Raw data length: {len(raw_data)} characters")
    print(f"Raw data preview: {raw_data[:200]}...")
    
    rows = raw_data.split('\n')
    parsed_data = []
    
    # Filter out empty rows and header rows
    data_rows = []
    for row in rows:
        row_stripped = row.strip()
        if row_stripped and not row_stripped.lower().startswith(('round', 'mb', 'name', 'credit')):
            # Skip header rows but keep data rows
            data_rows.append(row_stripped)
        elif row_stripped and row_stripped.lower().startswith('round'):
            # This is a data row with Round info
            data_rows.append(row_stripped)
    
    print(f"🔍 Found {len(data_rows)} data rows after filtering")
    for i, row in enumerate(data_rows[:5]):  # Show first 5
        print(f"   Row {i+1}: '{row}'")
    
    if not data_rows:
        print("❌ No data rows found after filtering")
        return parsed_data
        
    # Validate Round format and extract round number
    round_number = None
    
    for row_index, row in enumerate(data_rows):
        if not row.strip():
            continue
            
        print(f"🔍 Processing row {row_index + 1}: '{row}'")
            
        # Try different separators: tab, multiple spaces, single space, comma
        columns = []
        if '\t' in row:
            columns = [col.strip() for col in row.split('\t') if col.strip()]
            print(f"   Using tab separation: {columns}")
        elif '  ' in row:  # Multiple spaces
            columns = [col.strip() for col in row.split() if col.strip()]
            print(f"   Using space separation: {columns}")
        elif ',' in row:
            columns = [col.strip() for col in row.split(',') if col.strip()]
            print(f"   Using comma separation: {columns}")
        else:
            columns = [col.strip() for col in row.split() if col.strip()]
            print(f"   Using default split: {columns}")
            
        if len(columns) >= 2:
            try:
                round_info = columns[0].strip()
                member_value = columns[1].strip()
                
                print(f"   Round info: '{round_info}', Member value: '{member_value}'")
                
                # Extract and validate round number from "Round X" format
                round_match = re.search(r'round\s+(\d+)', round_info.lower())
                if not round_match:
                    print(f"❌ Invalid round format in row {row_index + 1}: '{round_info}' (expected 'Round X')")
                    continue  # Skip this row instead of returning empty
                
                current_round = int(round_match.group(1))
                print(f"   Extracted round number: {current_round}")
                
                # Validate that all rows have the same round number
                if round_number is None:
                    round_number = current_round
                    print(f"   Set round number to: {round_number}")
                elif round_number != current_round:
                    print(f"❌ Inconsistent round number in row {row_index + 1}: found 'Round {current_round}', expected 'Round {round_number}'")
                    continue  # Skip inconsistent rows instead of returning empty
                
                # Position is based on order in the parsed data (1st, 2nd, 3rd, etc.)
                position = len(parsed_data) + 1
                
                data_row = {
                    'round': round_number,
                    'position': position,
                    'name': member_value,  # The member number/ID goes into name field
                    'rank': f"{position}{'st' if position == 1 else 'nd' if position == 2 else 'rd' if position == 3 else 'th'}",
                    'member_id': member_value  # Also store as member_id for reference
                }
                parsed_data.append(data_row)
                print(f"   ✅ Added data row: Position={position}, Round={round_number}, Member={member_value}")
                
            except (ValueError, IndexError) as e:
                print(f"❌ Error parsing row {row_index + 1}: {e}")
                continue  # Skip problematic rows instead of returning empty
        else:
            print(f"❌ Insufficient columns in row {row_index + 1}: {len(columns)} columns found, need at least 2")
            continue  # Skip rows with insufficient data
            
    print(f"✅ Successfully parsed {len(parsed_data)} rows for Round {round_number}")
    return parsed_data

def test_data_parsing():
    """Test the data parsing with sample data"""
    
    # Test data from the screenshot
    test_data1 = """Round 1	60050
Round 1	555
Round 1	60111
Round 1	1002431
Round 1	1012353
Round 1	60192
Round 1	60238
Round 1	1006268
Round 1	60141
Round 1	83410"""

    print("=" * 60)
    print("Testing Tab-separated data:")
    print("=" * 60)
    result1 = parse_data(test_data1)
    print(f"\nParsed {len(result1)} rows:")
    for row in result1:
        print(f"  {row['rank']}: Member {row['name']} (Round {row['round']})")
    
    # Test with space-separated data (fix the parsing logic)
    test_data2 = """Round 1    60050
Round 1    555
Round 1    60111
Round 1    1002431
Round 1    1012353"""

    print("\n" + "=" * 60)
    print("Testing Space-separated data:")
    print("=" * 60)
    result2 = parse_data(test_data2)
    print(f"\nParsed {len(result2)} rows:")
    for row in result2:
        print(f"  {row['rank']}: Member {row['name']} (Round {row['round']})")

    # Test line-by-line format (like from the screenshot)
    test_data3 = """Round 1
60050
Round 1
555
Round 1
60111
Round 1
1002431
Round 1
1012353"""

    print("\n" + "=" * 60)
    print("Testing Line-by-line data (from screenshot):")
    print("=" * 60)
    result3 = parse_data(test_data3)
    print(f"\nParsed {len(result3)} rows:")
    for row in result3:
        print(f"  {row['rank']}: Member {row['name']} (Round {row['round']})")

    # Test with header rows (should be filtered out)
    test_data4 = """Round	MB	NAME	Credit	Last Bet
Round 1	60050	HO CUONG DIEU	30900	
Round 1	555	CHWEE WAI ONN	21180	
Round 1	60111	NGUYEN VAN A	15000	"""

    print("\n" + "=" * 60)
    print("Testing Data with headers:")
    print("=" * 60)
    result4 = parse_data(test_data4)
    print(f"\nParsed {len(result4)} rows:")
    for row in result4:
        print(f"  {row['rank']}: Member {row['name']} (Round {row['round']})")

if __name__ == "__main__":
    test_data_parsing()
