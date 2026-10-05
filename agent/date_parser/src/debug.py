import datetime
import dateparser

ref_date = datetime.date(2026, 10, 15)

print("this Monday:", dateparser.parse("this Monday", settings={'RELATIVE_BASE': datetime.datetime(2026, 10, 15)}))
print("next Monday:", dateparser.parse("next Monday", settings={'RELATIVE_BASE': datetime.datetime(2026, 10, 15)}))
print("the 15th:", dateparser.parse("the 15th", settings={'RELATIVE_BASE': datetime.datetime(2026, 10, 16), 'PREFER_DATES_FROM': 'future'}))
print("ISO:", dateparser.parse("2026-10-15t14:30:00z"))
print("kal:", dateparser.parse("kal", languages=['en', 'hi'], settings={'RELATIVE_BASE': datetime.datetime(2026, 10, 15)}))
