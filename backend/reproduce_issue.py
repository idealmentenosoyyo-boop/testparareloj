
import datetime
import time

def simulate_save_log(iteration):
    now = datetime.datetime.now()
    day_str = now.strftime('%Y-%m-%d')
    doc_id = now.strftime('%H%M%S_%f')
    print(f"Iter {iteration}: /devices/dev1/days/{day_str}/events/{doc_id}")

print("Simulating rapid events...")
for i in range(5):
    simulate_save_log(i)
    # No sleep, to test collision
