import requests

url = 'http://localhost:5000/api/courses/submissions/e0d0a930-4d89-4a53-84d2-da30fa08a8a5'
files = {'file': open('C:/Users/percy/OneDrive/Desktop/percy_resume.pdf', 'rb')}
data = {'user_id': 'e43282ea-8829-463e-87c0-cd59847d4f93', 'assignment': 'My Assignment', 'due_date': '2023-03-01T14:30:00.000Z'}

response = requests.post(url, files=files, data=data)

print(response.json())
