
import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
from datetime import datetime

# Setup Firebase
firebase_sa_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
if not firebase_sa_json:
    print("No FIREBASE_SERVICE_ACCOUNT")
    exit(1)

try:
    sa_dict = json.loads(firebase_sa_json)
    cred = credentials.Certificate(sa_dict)
    firebase_admin.initialize_app(cred)
except:
    cred = credentials.Certificate(firebase_sa_json)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Scan last 5 days
import datetime

# Device ID we want to check
device_id = '3707806493'

base = datetime.datetime.now()
date_list = [base - datetime.timedelta(days=x) for x in range(5)]

found_health = False

for date_obj in date_list:
    day_str = date_obj.strftime('%Y-%m-%d')
    print(f"\nChecking {day_str}...")
    
    events_ref = db.collection('devices').document(device_id).collection('days').document(day_str).collection('events')
    docs = events_ref.stream()
    
    day_count = 0
    for doc in docs:
        day_count += 1
        data = doc.to_dict()
        etype = data.get('event_type') or data.get('type')
        
        if etype in ['HEALTH', 'bphrt', 'oxygen', 'HEALTH_DATA']:
            print(f" ✅ FOUND HEALTH EVENT! ID: {doc.id} | Data: {data}")
            found_health = True
            
    if day_count == 0:
        print(f"  (No events)")
    else:
        print(f"  ({day_count} total events)")

if not found_health:
    print("\n❌ NO HEALTH DATA FOUND IN LAST 5 DAYS.")
    print("The 'last_hr' you see is likely very old or manually set.")

