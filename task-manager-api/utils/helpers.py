from utils.dates import format_date, utc_naive
from utils.validation import task_fields
from utils.constants import STATUSES as VALID_STATUSES, ROLES as VALID_ROLES, MAX_TITLE_LENGTH, MIN_TITLE_LENGTH, DEFAULT_PRIORITY
import re
import uuid
MIN_PASSWORD_LENGTH=4
DEFAULT_COLOR='#000000'

def calculate_percentage(part,total): return round(part/total*100,2) if total else 0

def validate_email(email): return isinstance(email,str) and bool(re.fullmatch(r'[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+',email))

def sanitize_string(value): return value.strip() if isinstance(value,str) else value

def generate_id(): return str(uuid.uuid4())

def log_action(action,details=None): print(f'[{utc_naive()}] ACTION: {action}')

def parse_date(value):
    from datetime import datetime
    for pattern in ('%Y-%m-%d','%d/%m/%Y'):
        try: return datetime.strptime(value,pattern)
        except (TypeError,ValueError): pass
    return None

def is_valid_color(value): return isinstance(value,str) and bool(re.fullmatch(r'#[0-9a-fA-F]{6}',value))

def process_task_data(data,existing_task=None):
    from errors import APIError
    try: return task_fields(data),None
    except APIError as error: return None,error.message
