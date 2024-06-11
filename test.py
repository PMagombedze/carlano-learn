import requests

url = 'http://localhost:5000/api/courses/submissions/5564cbbe-6c6c-4d1e-b1a8-d91d45c29202'
files = {'file': open('C:/Users/percy/OneDrive/Desktop/percy_resume.pdf', 'rb')}
data = {'user_id': 'e7b6ad17-78e7-44fa-bbd2-a83cb693b7ed', 'assignment': 'My Assignment', 'due_date': '2023-03-01T14:30:00.000Z'}

response = requests.post(url, files=files, data=data)

print(response.json())