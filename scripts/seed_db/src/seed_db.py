import os
import sys
import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def main():
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    
    default_db_path = base_dir / "data" / "availability_db" / "src" / "availability.db"
    default_prop_path = base_dir / "data" / "properties" / "src" / "properties.json"
    
    # Use the unified application settings singleton
    try:
        from agent.config.src.config import get_settings
        settings = get_settings()
        db_path = settings.db_path.resolve()
        prop_path = settings.properties_path.resolve()
    except ImportError:
        # Fallback if run standalone outside the package structure
        db_path = Path(os.environ.get("DB_PATH", default_db_path)).resolve()
        prop_path = Path(os.environ.get("PROPERTIES_PATH", default_prop_path)).resolve()
    
    # 1. Properties file checks
    if not prop_path.exists():
        eprint(f"Error: Source properties file not found at {prop_path}")
        sys.exit(1)
        
    try:
        with open(prop_path, 'r', encoding='utf-8') as f:
            properties = json.load(f)
    except json.JSONDecodeError:
        eprint(f"Error: Invalid JSON syntax in properties file at {prop_path}.")
        sys.exit(1)
        
    # Schema check
    if not isinstance(properties, list) or len(properties) == 0:
        eprint(f"Error: Schema mismatch in properties file. Missing required keys in element {properties}.")
        sys.exit(1)
        
    for prop in properties:
        if not isinstance(prop, dict) or "property_id" not in prop or "room_types" not in prop or not isinstance(prop["room_types"], list) or len(prop["room_types"]) == 0:
            eprint(f"Error: Schema mismatch in properties file. Missing required keys in element {prop}.")
            sys.exit(1)
            
    # Duplicate room check pre-emptively to give exact room_id error
    seen_rooms = set()
    for prop in properties:
        for room in prop["room_types"]:
            room_id = room.get("room_id")
            if room_id in seen_rooms:
                eprint(f"Error: Duplicate room_id '{room_id}' detected in properties. Database constraints violated.")
                sys.exit(1)
            seen_rooms.add(room_id)
            
    # 2. DB dir creation
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        eprint(f"Error: Could not create directory {db_path.parent}. Permission denied.")
        sys.exit(1)
        
    # 3. SQLite Schema
    try:
        conn = sqlite3.connect(db_path, timeout=1.0)
    except sqlite3.OperationalError as e:
        if "locked" in str(e).lower():
            eprint(f"Error: Database at {db_path} is locked by another process.")
            sys.exit(1)
        else:
            eprint(f"Error: Permission denied when writing to database at {db_path}.")
            sys.exit(1)
            
    cursor = conn.cursor()
    try:
        # Just a test write to catch permission errors before actual schema changes
        cursor.execute("PRAGMA synchronous = OFF;")
        
        cursor.execute("DROP TABLE IF EXISTS availability")
        cursor.execute("DROP TABLE IF EXISTS bookings")
        
        cursor.execute("""
            CREATE TABLE availability (
                property_id TEXT NOT NULL CHECK (length(property_id) > 0),
                room_id     TEXT NOT NULL CHECK (length(room_id) > 0),
                date        TEXT NOT NULL CHECK (date(date) IS NOT NULL AND date(date) = date),
                is_available INTEGER NOT NULL DEFAULT 1 CHECK (is_available IN (0, 1)),
                remaining_rooms INTEGER NOT NULL DEFAULT 1 CHECK (remaining_rooms >= 0),
                PRIMARY KEY (room_id, date),
                CHECK ((remaining_rooms > 0 AND is_available = 1) OR (remaining_rooms = 0 AND is_available = 0))
            ) STRICT;
        """)
        
        cursor.execute("CREATE INDEX idx_avail_prop_date ON availability(property_id, date, is_available);")
        
        cursor.execute("""
            CREATE TABLE bookings (
                booking_ref TEXT PRIMARY KEY NOT NULL CHECK (length(booking_ref) > 0),
                property_id TEXT NOT NULL CHECK (length(property_id) > 0),
                room_id     TEXT NOT NULL CHECK (length(room_id) > 0),
                check_in    TEXT NOT NULL CHECK (date(check_in) IS NOT NULL AND date(check_in) = check_in),
                check_out   TEXT NOT NULL CHECK (date(check_out) IS NOT NULL AND date(check_out) = check_out),
                guests      INTEGER NOT NULL CHECK (guests > 0),
                guest_name  TEXT COLLATE NOCASE,
                add_ons     TEXT CHECK (add_ons IS NULL OR json_valid(add_ons)),
                total_price REAL NOT NULL CHECK (total_price >= 0.0),
                status      TEXT NOT NULL DEFAULT 'hold' CHECK (status IN ('hold', 'confirmed', 'cancelled')),
                created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP CHECK (datetime(created_at) IS NOT NULL AND datetime(created_at) = created_at),
                CHECK (check_out > check_in)
            ) STRICT;
        """)
    except sqlite3.OperationalError as e:
        if "locked" in str(e).lower():
            eprint(f"Error: Database at {db_path} is locked by another process.")
            sys.exit(1)
        else:
            eprint(f"Error: Permission denied when writing to database at {db_path}.")
            sys.exit(1)

    start_date = date(2026, 10, 1)
    end_date = date(2026, 12, 31)
    
    delta = end_date - start_date
    dates = [start_date + timedelta(days=i) for i in range(delta.days + 1)]
    
    records = []
    
    num_properties = len(properties)
    
    # 4. Generate records
    for prop in properties:
        prop_id = prop["property_id"]
        for room in prop["room_types"]:
            room_id = room["room_id"]
            for d in dates:
                d_str = d.strftime("%Y-%m-%d")
                
                is_available = 1
                remaining_rooms = 5
                
                if room_id == "GOA001-POOL":
                    if d in [date(2026, 10, 9), date(2026, 10, 10), date(2026, 10, 11)]:
                        is_available = 0
                        remaining_rooms = 0
                elif room_id == "GOA002-COTTAGE":
                    if d in [date(2026, 10, 15), date(2026, 10, 16), date(2026, 10, 17)]:
                        is_available = 1
                        remaining_rooms = 1
                        
                records.append((prop_id, room_id, d_str, is_available, remaining_rooms))
                
    try:
        cursor.executemany("""
            INSERT INTO availability (property_id, room_id, date, is_available, remaining_rooms)
            VALUES (?, ?, ?, ?, ?)
        """, records)
        conn.commit()
    except sqlite3.IntegrityError as e:
        eprint(f"Error: Duplicate room_id detected in properties. Database constraints violated.")
        sys.exit(1)
    except sqlite3.OperationalError as e:
        if "locked" in str(e).lower():
            eprint(f"Error: Database at {db_path} is locked by another process.")
            sys.exit(1)
        else:
            eprint(f"Error: Permission denied when writing to database at {db_path}.")
            sys.exit(1)
            
    conn.close()
    
    print(f"Inserted {len(records)} availability records. {num_properties} properties processed. Database written to {db_path}")

if __name__ == "__main__":
    main()
