import pandas as pd
import re
from datetime import datetime


price_pattern = re.compile(r'\b[.,\d]+\b')
date_pattern = re.compile(r'\b[.,\-//\d]+\b')


def process_address(text):
    substring_to_remove = "Die vollständige Adresse der Immobilie erhalten Sie vom Anbieter."
    address = text.replace(substring_to_remove, '')
    address = address.replace('\n', ' ')
    return address


def process_area(text):
    substring_to_remove = "m²"
    area = str(text).replace(substring_to_remove, '').strip()
    area = float(area.replace(",", '.'))
    return area


def process_room(text):
    room = float(str(text).replace(",", '.'))
    return room


def process_price(text):
    substring_to_remove = "€"
    price = str(text).replace(substring_to_remove, '').strip()
    try:
        price = float(price.replace(".", '').replace(",", '.'))
    except ValueError:
        return None
    return price


def find_price(text):
    match = price_pattern.search(str(text))
    if match:
        result = match.group()
        try:
            price = float(result.replace(".", '').replace(",", '.'))
            return price
        except ValueError:
            return None
    else:
        return None


def replace_german_months(text):
    german_months = {
        'januar': '01',
        'februar': '02',
        'märz': '03',
        'april': '04',
        'mai': '05',
        'juni': '06',
        'juli': '07',
        'august': '08',
        'september': '09',
        'oktober': '10',
        'november': '11',
        'dezember': '12'
    }
    pattern = re.compile(r'\b(?:' + '|'.join(german_months.keys()) + r')\b', re.I)
    result = pattern.sub(lambda x: german_months[x.group().lower()], text)
    return result


def convert_to_datetime(text):
    text = replace_german_months(text)
    formats = [
        "%d.%m.%Y",
        "%Y-%m-%d",
        "%d.%m.%y",
        "%d %m %Y",
        "%d.%m.%y",
        "%d. %m %Y",
        "%m/%Y",
        "%m %Y",
        "%m %Y",
        "%d.%m.%Y"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(str(text), fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def find_date(text):
    text = str(text).lower()
    first_match = convert_to_datetime(text)
    if first_match:
        return first_match
    match = date_pattern.search(text)
    if match:
        result = match.group()
        return convert_to_datetime(result)
    elif "sofort" in text:
        return "sofort"
    else:
        return None


def find_year(text):
    try:
        return int(text)
    except ValueError:
        return None


