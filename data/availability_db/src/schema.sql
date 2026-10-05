CREATE TABLE availability (
    property_id TEXT NOT NULL CHECK (length(property_id) > 0),
    room_id     TEXT NOT NULL CHECK (length(room_id) > 0),
    date        TEXT NOT NULL CHECK (date(date) IS NOT NULL AND date(date) = date),   -- 'YYYY-MM-DD'
    is_available INTEGER NOT NULL DEFAULT 1 CHECK (is_available IN (0, 1)),
    remaining_rooms INTEGER NOT NULL DEFAULT 1 CHECK (remaining_rooms >= 0),
    PRIMARY KEY (room_id, date),
    CHECK ((remaining_rooms > 0 AND is_available = 1) OR (remaining_rooms = 0 AND is_available = 0))
) STRICT;

CREATE INDEX idx_avail_prop_date ON availability(property_id, date, is_available);

CREATE TABLE bookings (
    booking_ref TEXT PRIMARY KEY NOT NULL CHECK (length(booking_ref) > 0),
    property_id TEXT NOT NULL CHECK (length(property_id) > 0),
    room_id     TEXT NOT NULL CHECK (length(room_id) > 0),
    check_in    TEXT NOT NULL CHECK (date(check_in) IS NOT NULL AND date(check_in) = check_in),
    check_out   TEXT NOT NULL CHECK (date(check_out) IS NOT NULL AND date(check_out) = check_out),
    guests      INTEGER NOT NULL CHECK (guests > 0),
    guest_name  TEXT COLLATE NOCASE,
    guest_phone TEXT COLLATE NOCASE,
    add_ons     TEXT CHECK (add_ons IS NULL OR json_valid(add_ons)),
    total_price REAL NOT NULL CHECK (total_price >= 0.0),
    status      TEXT NOT NULL DEFAULT 'hold' CHECK (status IN ('hold', 'confirmed', 'cancelled')),
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP CHECK (datetime(created_at) IS NOT NULL AND datetime(created_at) = created_at),
    CHECK (check_out > check_in)
) STRICT;
