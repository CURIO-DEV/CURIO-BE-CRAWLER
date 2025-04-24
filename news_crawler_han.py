import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import datetime  

import time
import json

#썸네일 url 가져오기
def get_thumbnail_from_article(url):
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, 'html.parser')
        og_image = soup.select_one("meta[property='og:image']")
        if og_image:
            return og_image.get("content")
    except Exception as e:
        print(f"썸네일 가져오기 실패: {e}")
    return None

# 카테고리랑 등록일 가져오기
def get_category_and_created_at_from_article(url):
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, 'html.parser')

        # 1. 카테고리 가져오기
        breadcrumb = soup.select_one("div.ArticleDetailView_breadcrumb___UwRC")
        category = ""
        if breadcrumb:
            first_category = breadcrumb.find("a")
            if first_category:
                category = first_category.get_text(strip=True)

        # 2. 등록 시간 가져오기
        created_at = ""
        date_list = soup.select("ul.ArticleDetailView_dateList__tniXJ li")
        for li in date_list:
            if "등록" in li.get_text():
                time_span = li.find("span")
                if time_span:
                    created_at = time_span.get_text(strip=True)
                    break

        return category, created_at

    except Exception as e:
        print(f"카테고리/시간 가져오기 실패: {e}")
        return "", ""


def format_datetime(korean_time_str):
    try:
        dt = datetime.strptime(korean_time_str, "%Y-%m-%d %H:%M")
        return dt.isoformat()  # '2025-04-19T21:26:00'
    except Exception as e:
        print(f"날짜 포맷 에러: {e}")
        return "2025-04-19T00:00:00"  # fallback

def crawl_hani_latest_with_selenium():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    driver.get("https://www.hani.co.kr/arti")
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    articles = soup.select("a.BaseArticleCard_link__Q3YFK")

    results = []
    seen = set()
    for article in articles:
        href = article.get("href", "")
        if href in seen or not href:
            continue
        seen.add(href)

        title_div = article.select_one("div.BaseArticleCard_title__TVFqt")
        if not title_div:
            continue

        title = title_div.text.strip()
        full_url = "https://www.hani.co.kr" + href

        image_url = get_thumbnail_from_article(full_url)
        category, created_at = get_category_and_created_at_from_article(full_url)

        results.append({
            "title": title,
            "url": full_url,
            "image": image_url,
            "category": category,
            "createdAt": created_at
        })

        if len(results) >= 10:
            break

    driver.quit()
    return results




def send_to_spring_api(news_list):
    """
    이 함수는 크롤링한 news_list를 Spring API의 /curio/news/crawler 엔드포인트로 전송합니다.
    """
    spring_url = "http://localhost:8080/curio/news/crawler"  # Spring API URL (필요에 따라 수정)
    headers = {"Content-Type": "application/json"}

    modified_list = []
    for news in news_list:
        modified_news = {
            "title": news["title"],
            "content": "",                         # 내용 (현재는 비어 있지만, 필요 시 추가할 수 있음)
            "summaryShort": "",                    # 요약 (필요 시 채워야 함)
            "summaryMedium": "",                   # 중간 요약 (필요 시 추가)
            "summaryLong": "",                     # 긴 요약 (필요 시 추가)
            "category": news.get("category", ""),                    # 카테고리 (예시로 넣었으므로 적절하게 수정 필요)
            "likeCount": 0,  
            "imageUrl": news["image"],
            "sourceUrl": news["url"],
            "createdAt": format_datetime(news.get("createdAt", "2025-04-19 12:00")),    
            "updatedAt": format_datetime(news.get("createdAt", "2025-04-19 12:00"))
            
        }
        modified_list.append(modified_news)

    response = requests.post(spring_url, json=modified_list, headers=headers)

    if response.status_code == 200:
        print("Data successfully sent to Spring API")
    else:
        print(f"Failed to send data: {response.status_code}, {response.text}")

if __name__ == "__main__":
    # 크롤링 실행
    results = crawl_hani_latest_with_selenium()
    
    # 결과 JSON 출력 (디버깅용)
    print(json.dumps(results, ensure_ascii=False))
    
    # Spring API로 결과 전송
    send_to_spring_api(results)
