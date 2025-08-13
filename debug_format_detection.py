#!/usr/bin/env python3
"""
Debug format detection logic
"""
import re

def debug_format_detection():
    # Line-by-line data from screenshot
    line_data = """Round 1
60050
Round 1
555
Round 1
60111
Round 1
1002431
Round 1
1012353"""
    
    # Space-separated data
    space_data = """Round 1    60050
Round 1    555
Round 1    60111
Round 1    1002431
Round 1    1012353"""
    
    for name, raw_data in [("Line-by-line", line_data), ("Space-separated", space_data)]:
        print(f"\n=== Testing {name} ===")
        print(f"Raw data: {repr(raw_data)}")
        
        rows = raw_data.split('\n')
        clean_rows = [row.strip() for row in rows if row.strip()]
        
        print(f"Clean rows: {clean_rows}")
        
        # Format detection
        columnar_format = False
        line_by_line_format = False
        
        # Check for columnar format - look for rows that have "Round X" and a number on the same line
        print("\n--- Checking columnar format ---")
        for i, row in enumerate(clean_rows[:5]):  # Check first 5 rows
            print(f"Row {i+1}: '{row}'")
            if '\t' in row or ('round' in row.lower() and len(row.split()) >= 2):
                # Check if it looks like "Round 1 60050" or "Round 1\t60050"
                parts = row.split('\t') if '\t' in row else row.split()
                print(f"  Parts: {parts}")
                if len(parts) >= 2:
                    # For 3+ parts like "Round 1 60050", check if first two parts form "Round X"
                    if len(parts) >= 3:
                        round_part = f"{parts[0]} {parts[1]}"  # "Round 1"
                        number_part = parts[2]  # The member ID
                    else:
                        round_part = parts[0]  # "Round1" or similar
                        number_part = parts[1]  # The member ID
                    
                    print(f"  Round part: '{round_part}', Number part: '{number_part}'")
                    
                    round_match = re.search(r'round\s*\d+', round_part.lower())
                    is_number = number_part.isdigit() and len(number_part) > 2
                    
                    print(f"  Round match: {round_match is not None}, Is long number: {is_number}")
                    
                    if round_match and is_number:
                        columnar_format = True
                        print(f"  -> Detected as COLUMNAR format!")
                        break
        
        # Check for line-by-line format - alternating "Round X" and number lines
        print("\n--- Checking line-by-line format ---")
        if not columnar_format and len(clean_rows) >= 2:
            consecutive_round_lines = 0
            
            for i in range(0, min(len(clean_rows), 10), 2):  # Check pairs
                if i + 1 < len(clean_rows):
                    line1 = clean_rows[i].strip()
                    line2 = clean_rows[i + 1].strip()
                    
                    print(f"  Pair {i//2 + 1}: '{line1}' + '{line2}'")
                    
                    # Check if line1 is "Round X" and line2 is a number
                    round_match = re.search(r'^round\s+\d+$', line1.lower())
                    is_number = line2.isdigit() and len(line2) > 2
                    
                    print(f"    Round match: {round_match is not None}, Is number: {is_number}")
                    
                    if round_match and is_number:
                        consecutive_round_lines += 1
                        print(f"    -> Valid pair! Count: {consecutive_round_lines}")
                    else:
                        print(f"    -> Invalid pair, breaking")
                        break
            
            # If we found at least 2 consecutive pairs, it's likely line-by-line format
            if consecutive_round_lines >= 2:
                line_by_line_format = True
                print(f"  -> Detected as LINE-BY-LINE format!")
        
        print(f"\nFINAL RESULT: Columnar={columnar_format}, Line-by-line={line_by_line_format}")

if __name__ == "__main__":
    debug_format_detection()
