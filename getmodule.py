import requests
from dotenv import load_dotenv
import os
import urllib.request
import re
import json
from sentence_transformers import SentenceTransformer, util
import numpy as np
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnableMap
from langchain_community.chat_models import ChatOllama
from langchain.schema.runnable import RunnableMap

##gpt 생성시 딕셔너리 외의 단어가 나올 수 있기 때문에 {.*}로 딕셔너리만 파싱한다.



load_dotenv()




#쇼핑 디코딩
def parse_shoping_data(data):
        
    items = data['items']
    total = data["total"]
    porducts = []
    productType_decoder = {
    "1": "일반상품 가격비교 상품",
    "2": "일반상품 가격비교 비매칭 일반상품",
    "3": "일반상품 가격비교 매칭 일반상품",
    "4": "중고상품 가격비교 상품",
    "5": "중고상품 가격비교 비매칭 일반상품",
    "6": "중고상품 가격비교 매칭 일반상품",
    "7": "단종상품 가격비교 상품",
    "8": "단종상품 가격비교 비매칭 일반상품",
    "9": "단종상품 가격비교 매칭 일반상품",
    "10": "판매예정상품 가격비교 상품",
    "11": "판매예정상품 가격비교 비매칭 일반상품",
    "12": "판매예정상품 가격비교 매칭 일반상품"
}

    for item in items:
        info = {
            '상품 이름': item.get('title'),
            '상품 링크': item.get('link'),
            '상품 이미지': item.get('image'),
            '상품 최고가': item.get('hprice'),
            '상품 최저가': item.get('lprice'),
            '쇼핑몰 정보': item.get('mallName'),
            '상품 타입': productType_decoder.get(item.get('productType')),
            '제조사': item.get('maker'),
            '브랜드': item.get('brand'),
            '대분류 카테고리': item.get('category1'),
            '중분류 카테고리': item.get('category2'),
            '소분류 카테고리': item.get('category3'),
            '세분류 카테고리': item.get('category4'),
        }
        porducts.append(info)
    return 


exclude = "" """ #검색 결과에서 제외할 상품 유형. exclude={option}:{option}:{option} 형태로 설정합니다(예: exclude=used:cbshop).
                - used: 중고
                - rental: 렌탈
                - cbshop: 해외직구, 구매대행
                """

def make_query(input):
    sort_list = [
        "정확도순",
        "날짜순",
        "최고가",
        "최저가",
        "기본"
    ]
    template = """
        너는 사용자의 질문에서 검색 쿼리와 정렬 쿼리를 찾는 모델이야.
        정렬 쿼리 리스트는 다음과 같아
        {sort_list}
        정렬 쿼리는 반드시 정렬 쿼리 리스트 내에서 반환해줘.
        사용자의 질문에서 검색 쿼리 키워드를 찾아줘. 
        사용자의 질문에서 검색 개수를 찾아줘. 검색 개수는 반드시 숫자로 반환해줘야해.
        만약 검색 개수에 대한 정보가 없다면 검색 개수는 0으로 반환해줘.
        쿼리별 배열의 길이는 모두 같아야해.

        반드시 다음 형식으로 대답해줘:
        {{
            "정렬 쿼리": ["정렬쿼리 리스트 내의 값"],
            "검색 쿼리": ["문장에서 뽑아낸 검색 키워드"]
            "검색 개수": ["문장에서 뽑아낸 검색 개수"]
        }}
        예시는 다음과 같아:
        사용자: 쇼핑몰에서 최저가 순으로 참치를 10개 검색해줘
        답변: {{"정렬 쿼리": ["최저가"], "검색 쿼리": ["참치"], "검색 개수": [10]}}

        사용자: 가격이 낮은 컴퓨터 검색해줘
        답변: {{"정렬 쿼리": ["최저가"], "검색쿼리": ["컴퓨터"], "검색 개수": [0]}}

        사용자: 네네치킨과 굽네치킨을 가격이 낮은 순으로 검색해줘
        답변: {{"정렬 쿼리": ["최저가", "최저가"], "검색쿼리": ["네네치킨", "굽네치킨"], "검색 개수": [0,0]}}

        사용자: 인형은 10개를 낮은 가격순으로, 양말은 5개를 높은 가격순으로 검색해줘
        답변: {{"정렬 쿼리": ["최저가", "최고가"], "검색쿼리": ["인형", "양말"], "검색 개수": [10,5]}}

        이제 너가 대답해줄 차례야
        사용자: {question} 
        """
    #프롬포트를 통해 few-shot 인코딩 적용으로, 좀더 정확한 쿼리가 나올 수 있도록 설계
    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatOllama(model="gemma2:9b", temperature=0, base_url="http://127.0.0.1:11434/") #http://127.0.0.1:11434
    chain = RunnableMap({
    "sort_list": lambda x: x["sort_list"],
    "question": lambda x: x["question"]
    }) | prompt | llm  
    return chain.invoke({'question': f"{input}","sort_list":f"{',' .join(sort_list)}"}).content
    #프롬포트에 sort_list를 전달, 쿼리가 나오도록 전달해줌.


def make_url(query:str):
    try:
        query_clean = re.search(r'\{.*?\}', query, re.DOTALL)
        print(query_clean.group(0))
        query_dict = json.loads(query_clean.group(0))
    except Exception as e:
        return {"error":"검색 쿼리 생성을 실패했습니다.","Exception":f"{e}"}
    sort_errors = [False for _ in range(len(query_dict["검색 쿼리"]))]
    item_len_errors = [False for _ in range(len(query_dict["검색 쿼리"]))]
    pageable = 1
    sort_decoder = {
    "기본" : "sim",
    "정확도순":"sim",
    "날짜순":"data",
    "최고가":"asc",
    "최저가":"dsc"
    }
    base_urls = []
    try:
        for idx in range(len(query_dict["검색 쿼리"])):
            try:
                sort = sort_decoder[f"{query_dict['정렬 쿼리'][idx]}"]
            except:
                sort = "sim"
                sort_errors[idx] = True
            try:
                serach = f"{query_dict['검색 쿼리'][idx]}"
            except Exception as e:
                return {"error":"검색 쿼리를 발견하지 못했습니다.","Exception":f"{e}"}
            try:
                len_item = int(f"{query_dict['검색 개수'][idx]}")
            except:
                len_item = 10
                item_len_errors[idx] = True
            
            pageable = len_item // 100
            pageable += 1
            
            page_list= []
            for idx in range(pageable):
                start_index = idx * 100  
                # display_len 계산
                display_len = len_item - start_index if len_item - start_index >= 100 else len_item - start_index
                
                # display_len이 0이 아닌 경우에만 URL 추가
                if display_len > 0:
                    base_urls.append(f"https://openapi.naver.com/v1/search/shop?query={serach}&sort={sort}&start_page={idx + 1}&display_len={display_len}")
            base_urls.append(page_list)

    except Exception as e:
        return {"error":"검색할 상품을 발견하지 못했습니다.","Exception":f"{e}"}
    
    error_msgs=[]
    try:
        for sort_error, item_len_error,item in zip(sort_errors,item_len_errors,query_dict["검색 쿼리"]):
            msg = ""
            sortmsg = ""
            lenmgs = ""
            if sort_error:
                sortmsg = f"{item}의 정렬 기준을 찾을 수 없어 기본값인 정확도를 기준으로 검색했습니다.\n"
            if item_len_error:
                lenmgs = f"{item}의 찾을 개수를 찾지 못해 기본값인 10개로 검색했습니다.\n"
            msg = sortmsg+lenmgs
            if msg=="":
                pass
            else:
                error_msgs.append(msg) 
    except Exception as e:
        return{"error":f"","base_urls":base_urls}

    return {"error":f"{error_msgs}","base_urls":base_urls}

def request_for_serach_engen(base_urls:list):
    headers = {
        "X-Naver-Client-Id": os.getenv("X-Naver-Client-Id"),
        "X-Naver-Client-Secret": os.getenv("X-Naver-Client-Secret")
    }
    
    data_list = []
    for urls in base_urls:
        
        for url in urls:
            try:
                response = requests.get(url,headers=headers)
                if response.status_code == 200:
                    data_list
                else:

                    continue
            except Exception as e:
                

query = make_query("양말과 네네치킨의 최저가 10개씩 검색해줘")
print(make_url(query))

query = make_query("양말과 네네치킨의 최저가 500개씩 검색해줘")
print(make_url(query))

# 
# response = requests.get(base_url,headers=headers)
# # print(response.content.decode("utf-8"))

# modified_text = re.sub(r'<.*?>', '', response.content.decode("utf-8"))
# print(modified_text)
# print(parse_shoping_data(json.loads(modified_text)))
