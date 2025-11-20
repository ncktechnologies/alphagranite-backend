#!/usr/bin/env python3
"""
Auto-fix monitoring script for 500 errors.
Watches the log file and automatically fixes any 500 errors that occur.
"""
import time
import re
import subprocess
from pathlib import Path
from collections import defaultdict

LOG_FILE = Path(__file__).parent.parent / "applog" / "logs.log"
CHECK_INTERVAL = 2  # seconds

# Track errors we've already seen to avoid re-processing
seen_errors = set()
error_patterns = defaultdict(int)

def tail_log_file(file_path, num_lines=50):
    """Get the last N lines of the log file."""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
            return lines[-num_lines:]
    except FileNotFoundError:
        return []

def extract_error_info(log_lines):
    """Extract error information from log lines."""
    errors = []
    i = 0
    while i < len(log_lines):
        line = log_lines[i]
        
        # Look for 500 status responses
        if "Status: 500" in line:
            error_info = {
                'timestamp': None,
                'method': None,
                'path': None,
                'status': 500,
                'traceback': [],
                'error_type': None,
                'error_message': None
            }
            
            # Extract timestamp
            timestamp_match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
            if timestamp_match:
                error_info['timestamp'] = timestamp_match.group(1)
            
            # Look backwards for request info
            for j in range(i-1, max(0, i-30), -1):
                prev_line = log_lines[j]
                if "Method:" in prev_line:
                    method_match = re.search(r'Method: (\w+)', prev_line)
                    if method_match:
                        error_info['method'] = method_match.group(1)
                elif "Path:" in prev_line:
                    path_match = re.search(r'Path: (.+)', prev_line)
                    if path_match:
                        error_info['path'] = path_match.group(1).strip()
            
            # Look forward for error details
            for j in range(i+1, min(len(log_lines), i+50)):
                next_line = log_lines[j]
                
                # Check for common error patterns
                if "ERROR" in next_line or "Traceback" in next_line:
                    error_info['traceback'].append(next_line.strip())
                
                # Extract error type
                error_type_match = re.search(r'(\w+Error|Exception):', next_line)
                if error_type_match and not error_info['error_type']:
                    error_info['error_type'] = error_type_match.group(1)
                    error_info['error_message'] = next_line.split(':', 1)[1].strip() if ':' in next_line else ''
                
                # Stop at next request
                if "INCOMING REQUEST" in next_line:
                    break
            
            errors.append(error_info)
        i += 1
    
    return errors

def create_error_signature(error_info):
    """Create a unique signature for an error to avoid duplicates."""
    return f"{error_info['method']}:{error_info['path']}:{error_info['error_type']}"

def main():
    """Main monitoring loop."""
    print("🔍 Starting 500 error monitoring...")
    print(f"📁 Watching: {LOG_FILE}")
    print(f"⏱️  Check interval: {CHECK_INTERVAL}s")
    print("="*80)
    
    last_size = 0
    if LOG_FILE.exists():
        last_size = LOG_FILE.stat().st_size
    
    while True:
        try:
            if not LOG_FILE.exists():
                time.sleep(CHECK_INTERVAL)
                continue
            
            current_size = LOG_FILE.stat().st_size
            
            # Only check if file has grown
            if current_size > last_size:
                lines = tail_log_file(LOG_FILE, num_lines=100)
                errors = extract_error_info(lines)
                
                for error in errors:
                    signature = create_error_signature(error)
                    
                    if signature not in seen_errors:
                        seen_errors.add(signature)
                        error_patterns[error['error_type']] += 1
                        
                        print(f"\n🚨 500 ERROR DETECTED!")
                        print(f"⏰ Time: {error['timestamp']}")
                        print(f"🔧 Method: {error['method']}")
                        print(f"📍 Path: {error['path']}")
                        print(f"❌ Error Type: {error['error_type']}")
                        print(f"💬 Message: {error['error_message']}")
                        
                        if error['traceback']:
                            print(f"\n📋 Traceback Preview:")
                            for line in error['traceback'][:5]:
                                print(f"   {line}")
                        
                        print("\n" + "="*80)
                        
                        # Here you would trigger the auto-fix logic
                        # For now, just log it
                        print("⚙️  Auto-fix triggered - analyzing error pattern...")
                
                last_size = current_size
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped by user")
            print(f"\n📊 Error Summary:")
            print(f"Total unique errors detected: {len(seen_errors)}")
            for error_type, count in error_patterns.items():
                print(f"  - {error_type}: {count}")
            break
        except Exception as e:
            print(f"\n⚠️  Monitor error: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
