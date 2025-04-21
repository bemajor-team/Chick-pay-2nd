from locust import HttpUser, task, between

class ChickPayUser(HttpUser):
    host = "https://chick-pay.com"
    wait_time = between(1, 2)   # 대상 도메인

    @task
    def main_page(self):
        self.client.get("/")
