from locust import HttpUser, task, between
# from bs4 import BeautifulSoup

class MyUser(HttpUser):
    wait_time = between(1, 3)

    sessionid = "v7bcuquljzplonhi0sfqr4izid6mmo07"
    csrftoken = "qSmwfUOGThB0Ms5fsNOLdO3X9r2nVTvN"


    @task
    def load_main_page(self):
        self.client.get("/")  # 루트 페이지 요청

    @task
    def load_api_data(self):
        self.client.get("/zapp/cash/deposit/")  # API 요청

    # def on_start(self):
    #     """시작 시 로그인 처리"""
    #     self.username = "a123@a123.com"
    #     self.password = "123123"
    #     self.login()

    # def login(self):
    #     # 1. GET 로그인 페이지 → csrftoken 획득
    #     with self.client.get("/zapp/login", catch_response=True) as response:
    #         csrftoken = response.cookies.get("csrftoken", "")

    #     # 2. POST 로그인
    #     login_data = {
    #         "username": self.username,
    #         "password": self.password
    #     }
    #     headers = {
    #         "Content-Type": "application/json",
    #         "X-CSRFToken": csrftoken
    #     }
    #     self.client.post(
    #         "/zapp/login",
    #         data=login_data,
    #         headers=headers
    #     )

    @task
    def deposit_cash(self):
        # # csrftoken + sessionid 쿠키 가져오기
        # sessionid = self.client.cookies.get("sessionid", "")
        # csrftoken = self.client.cookies.get("csrftoken", "")
        # if not sessionid or not csrftoken:
        #     return  # 로그인 실패 시 스킵

        headers = {
            "Content-Type": "application/json",
            "X-CSRFToken": self.csrftoken,
            "Cookie": f"sessionid={self.sessionid}; csrftoken={self.csrftoken}"
        }

        payload = {
            "amount": 10000,
            "memo": "Locust 자동 입금 테스트"
        }

        self.client.post("/zapp/cash/deposit/", json=payload, headers=headers)
