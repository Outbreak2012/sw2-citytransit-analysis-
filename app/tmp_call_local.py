import os
import requests

token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhZG1pbkBjaXR5dHJhbnNpdC5jb20iLCJpYXQiOjE3NjI4MTE5NDIsImV4cCI6MTc2Mjg5ODM0Mn0.ENJOSQXnHFQez1JjVShVHYvDoxUwlCimPzDDsNA9b28"
url = 'http://127.0.0.1:8000/api/v1/analytics/demand/predict'
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json', 'Accept': 'application/json'}
json_data = {'route_id': 1, 'hours_ahead': 6}

r = requests.post(url, headers=headers, json=json_data, timeout=10)
print('status', r.status_code)
print('text', r.text)
