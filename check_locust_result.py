import pandas as pd
import sys

# CSV 로드
try:
    df = pd.read_csv('locust_result_stats.csv')
except FileNotFoundError:
    print("❌ 결과 CSV 파일을 찾을 수 없습니다.")
    sys.exit(1)

# "Total" 행 필터링
filtered = df[df['Name'] == "Aggregated"]

if filtered.empty:
    print('❌ "Total" row not found in Locust result.')
    sys.exit(1)

# 평균 응답시간 체크 (1초 = 1000ms) #일단 10000초
avg_response_time = filtered["Average Response Time"].values[0]
if avg_response_time > 10000:
    print(f"❌ 평균 응답시간 {avg_response_time}ms 초과: 실패")
    sys.exit(1)

# 에러율 체크
failure_count = filtered["Failure Count"].values[0]
request_count = filtered["Request Count"].values[0]

# 분모 0 예외 방지
if request_count == 0:
    print("❌ 요청 수가 0이라 에러율 계산 불가")
    sys.exit(1)

error_rate = (failure_count / request_count) * 100
if error_rate > 2:
    print(f"❌ 에러율 {error_rate:.2f}% 초과: 실패")
    sys.exit(1)

print("✅ 성능 기준 통과")

