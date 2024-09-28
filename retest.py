import re
import requests
import requests
from dotenv import load_dotenv
import os
import pprint
url = "https://openapi.naver.com/v1/search/shop?query=네네치킨&sort=dsc&start_page=3&display_len=3"

load_dotenv()

headers = {
        "X-Naver-Client-Id": os.getenv("X-Naver-Client-Id"),
        "X-Naver-Client-Secret": os.getenv("X-Naver-Client-Secret")
    }

response = requests.get(url,headers=headers)

pprint.pprint(response.json())

print(response.json()["total"])