import pytz

def convert_to_jst(utc_datetime):
    utc_zone = pytz.utc
    jst_zone = pytz.timezone('Asia/Tokyo')
    if utc_datetime.tzinfo is None:
        utc_zone = pytz.utc
        utc_datetime = utc_zone.localize(utc_datetime)
    jst_datetime = utc_datetime.astimezone(jst_zone)
    return jst_datetime.strftime('%Y/%m/%d %H:%M (JST)')