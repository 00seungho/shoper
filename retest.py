import re

url = "https://openapi.naver.com/v1/search/shop?query=네네치킨&sort=dsc&start_page=1&display_len=500"

# 정규 표현식으로 query 파라미터 추출
match = re.search(r'query=([^&]+)', url)
if match:
    query_value = match.group(1)  # '양말' 추출
    print(query_value)