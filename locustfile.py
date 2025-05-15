import random
from locust import HttpUser, task, between

# 헤더 없이 이메일만 줄줄이 있는 users.csv 파일 읽기
with open("users.csv", "r") as f:
    USER_EMAILS = [line.strip().strip('"') for line in f if line.strip()]

DEFAULT_PASSWORD = "Ab123456"

class ChickPayUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        self.email = random.choice(USER_EMAILS)

        login_response = self.client.post("/zapp/api/login/", json={
            "email": self.email,
            "password": DEFAULT_PASSWORD
        })

        if login_response.status_code != 200:
            print(f"❌ 로그인 실패: {self.email} | 응답: {login_response.status_code} | {login_response.text}")
            raise Exception("로그인 실패")
        self.session_cookie = login_response.cookies.get('sessionid')
        self.csrf_token = login_response.cookies.get('csrftoken')

    @task
    def hit_main_page(self):
        headers = {
            "Cookie": f"sessionid={self.session_cookie}; csrftoken={self.csrf_token}",
            "X-CSRFToken": self.csrf_token
        }
        self.client.get("/", headers=headers)
