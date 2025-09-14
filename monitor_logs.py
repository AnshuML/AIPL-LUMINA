#!/usr/bin/env python3
"""
Real-time log monitoring script
"""

import os
import time
import json
from datetime import datetime

def monitor_logs():
    """Monitor logs in real-time"""
    print("🔍 Starting log monitoring...")
    print("Press Ctrl+C to stop")
    
    logs_dir = "logs"
    last_queries = 0
    last_logins = 0
    
    try:
        while True:
            # Check queries
            queries_file = os.path.join(logs_dir, "queries.json")
            if os.path.exists(queries_file):
                with open(queries_file, 'r', encoding='utf-8') as f:
                    queries = json.load(f)
                    if len(queries) > last_queries:
                        print(f"📝 NEW QUERY DETECTED! Total queries: {len(queries)}")
                        latest_query = queries[-1]
                        print(f"   User: {latest_query['data']['user_email']}")
                        print(f"   Question: {latest_query['data']['question'][:50]}...")
                        print(f"   Time: {latest_query['timestamp']}")
                        last_queries = len(queries)
            
            # Check logins
            logins_file = os.path.join(logs_dir, "user_logins.json")
            if os.path.exists(logins_file):
                with open(logins_file, 'r', encoding='utf-8') as f:
                    logins = json.load(f)
                    if len(logins) > last_logins:
                        print(f"👤 NEW LOGIN DETECTED! Total logins: {len(logins)}")
                        latest_login = logins[-1]
                        print(f"   User: {latest_login['data']['user_email']}")
                        print(f"   Name: {latest_login['data']['user_name']}")
                        print(f"   Time: {latest_login['timestamp']}")
                        last_logins = len(logins)
            
            time.sleep(2)  # Check every 2 seconds
            
    except KeyboardInterrupt:
        print("\n🛑 Log monitoring stopped")

if __name__ == "__main__":
    monitor_logs()
