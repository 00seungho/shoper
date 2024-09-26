import requests
from dotenv import load_dotenv
import os
import urllib.request
serviceid = "shop"
load_dotenv()
serach_item = "진주" #아이템 카테고리
ascii_text = serach_item.encode('ascii', 'ignore')
display_len = "" #한번에 표시할 상품 갯수 기본 10개, 최대 100개
start_page = "" #검색 시작 위치 기본 1 최대 100
sort = "" #검색 결과 정렬, sim 정확도순, data 날짜순, asc 가격순 오름차순, dsc 가격순 내림차순
filter = "" #검색 결과에 포함할 상품 유형, 기본 설정안함, naverpay 네이버페이 연동 상품
exclude = "" """ #검색 결과에서 제외할 상품 유형. exclude={option}:{option}:{option} 형태로 설정합니다(예: exclude=used:cbshop).
                - used: 중고
                - rental: 렌탈
                - cbshop: 해외직구, 구매대행
                """
base_url = f"https://openapi.naver.com/v1/search/{serviceid}?query={ascii_text}"
headers = {
    "X-Naver-Client-Id": os.getenv("X-Naver-Client-Id"),
    "X-Naver-Client-Secret": os.getenv("X-Naver-Client-Secret"),
}
response = requests.get(base_url,headers=headers)

