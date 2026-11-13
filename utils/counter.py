import os

COUNTER_FILE = "data/counter.txt"

def get_next_id() -> int:
    os.makedirs("data", exist_ok=True)
    
    if not os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "w") as f:
            f.write("0")
    
    with open(COUNTER_FILE, "r") as f:
        current = int(f.read().strip() or "0")
    
    next_id = current + 1
    
    with open(COUNTER_FILE, "w") as f:
        f.write(str(next_id))
    
    return next_id