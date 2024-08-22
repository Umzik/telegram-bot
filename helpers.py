# helpers.py
import requests
from datetime import datetime, timedelta

from config import BACKEND_URL

TIME_FRAME_OPTIONS = {
    'Today': 'today',
    'Last 3 Days': 'last_3_days',
    'This Week': 'week',
    'This Month': 'month',
    'Custom': 'custom'
}

def calculate_date_range(option):
    today = datetime.now().date()
    
    if option == 'Today':
        return today, today
    elif option == 'Last 3 Days':
        end_date = today
        start_date = today - timedelta(days=2)
        return start_date, end_date
    elif option == 'This Week':
        end_date = today
        start_date = today - timedelta(days=today.weekday())
        return start_date, end_date
    elif option == 'This Month':
        end_date = today
        start_date = today.replace(day=1)
        return start_date, end_date
    else:
        return None, None

def get_user_token(login, password):
    response = requests.post(f"{BACKEND_URL}/login/", json={"login": login, "password": password}, verify=False)
    if response.status_code == 200:
        return response.json().get('access'), response.json().get('role'), response.json().get('role'), response.json().get('role')
    return None

def user_is_admin(token):
    response = requests.get(f"{BACKEND_URL}/is_admin/", headers={'Authorization': f'Bearer {token}'})
    return response.json().get("is_admin", False)
