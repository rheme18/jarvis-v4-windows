# tools/phone_lookup.py
import phonenumbers
from phonenumbers import geocoder, carrier, timezone

def lookup_phone_number_details(phone_number: str) -> str:
    try:
        parsed_number = phonenumbers.parse(phone_number, None)
        status = "Valid" if phonenumbers.is_valid_number(parsed_number) else "Invalid"
        
        country_code = "+" + phone_number[1:3] if phone_number.startswith("+") else "None"
        
        try: operator = carrier.name_for_number(parsed_number, "en") or "None"
        except: operator = "None"
            
        try:
            timezones = timezone.time_zones_for_number(parsed_number)
            timezone_info = timezones[0] if timezones else "None"
        except: timezone_info = "None"
            
        try: country = phonenumbers.region_code_for_number(parsed_number) or "None"
        except: country = "None"
            
        try: region = geocoder.description_for_number(parsed_number, "en") or "None"
        except: region = "None"
            
        try: formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL)
        except: formatted_number = "None"
            
        # Orijinal number_type belirleme döngüsü (Birebir korundu patron)
        number_type = "Unknown"
        ntype = phonenumbers.number_type(parsed_number)
        if ntype == phonenumbers.PhoneNumberType.MOBILE: number_type = "Mobile"
        elif ntype == phonenumbers.PhoneNumberType.FIXED_LINE: number_type = "Fixed Line"

        report = [
            f"📱 [TELEFON İSTİHBARAT RAPORU]",
            f" 🔹 Phone        : {phone_number}",
            f" 🔹 Formatted    : {formatted_number}",
            f" 🔹 Status       : {status}",
            f" 🔹 Country Code : {country_code}",
            f" 🔹 Country      : {country}",
            f" 🔹 Region       : {region}",
            f" 🔹 Timezone     : {timezone_info}",
            f" 🔹 Operator     : {operator}",
            f" 🔹 Type Number  : {number_type}"
        ]
        return "\n".join(report)
    except:
        return f"❌ {phone_number} geçersiz bir formatta patron!"