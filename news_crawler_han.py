import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import datetime  
import time
import json

# 썸네일 URL 가져오기
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

# 기사 본문 가져오기
def get_content_from_article(url):
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # 요청 실패 시 예외 발생
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.select("p.text")  # 본문 텍스트 부분
        content = "\n".join(p.get_text(strip=True) for p in paragraphs)
        return content
    except Exception as e:
        print(f"[ERROR] Failed to fetch content from {url} - {e}")
        return ""

# 날짜 포맷팅 함수
def format_datetime(korean_time_str):
    try:
        dt = datetime.strptime(korean_time_str, "%Y-%m-%d %H:%M")
        return dt.isoformat()  # '2025-04-19T21:26:00'
    except Exception as e:
        print(f"날짜 포맷 에러: {e}")
        return "2025-04-19T00:00:00"  # fallback

# 크롤링 실행
def crawl_hani_latest_with_selenium():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    driver.get("https://www.hani.co.kr/arti")
    time.sleep(2)
    
    # 무한 스크롤 가능하도록 
    SCROLL_PAUSE_TIME = 2
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

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
        content = get_content_from_article(full_url)  # 본문 내용 크롤링

        results.append({
            "title": title,
            "url": full_url,
            "image": image_url,
            "category": category,
            "createdAt": created_at,
            "content": content  # 본문 내용 추가
        })

        if len(results) >= 30:
            break

    driver.quit()
    return results

# Spring API로 전송
def send_to_spring_api(news_list):
    """
    이 함수는 크롤링한 news_list를 Spring API의 /curio/news/crawler 엔드포인트로 전송합니다.
    """
    # spring_url = "http://localhost:8080/curio/api/articles/crawler"  
    spring_url = "https://api.curi-o.site/curio/api/articles/crawler" # 배포 Spring API URL
    headers = {"Content-Type": "application/json"}

    modified_list = []
    for news in news_list:
        # 날짜 포맷을 처리하고, 생성 시간 정보가 없으면 기본 날짜를 사용
        created_at = news.get("createdAt", "")
        if not created_at:
            created_at = "2025-04-19 12:00"  # 기본 날짜
        formatted_date = format_datetime(created_at)

        modified_news = {
            "title": news["title"],
            "content": news["content"],  # 본문 내용 추가
            "summaryShort": "",          # 요약 (필요 시 채워야 함)
            "summaryMedium": "",         # 중간 요약 (필요 시 추가)
            "summaryLong": "",           # 긴 요약 (필요 시 추가)
            "category": news.get("category", ""),  # 카테고리
            "likeCount": 0,  
            "imageUrl": news["image"],
            "sourceUrl": news["url"],
            "createdAt": formatted_date,    
            "updatedAt": formatted_date
        }
        modified_list.append(modified_news)

    response = requests.post(spring_url, json=modified_list, headers=headers)

    if response.status_code == 200:
        print("Data successfully sent to Spring API")
    else:
        print(f"Failed to send data: {response.status_code}, {response.text}")
        
        
def crawl_hani_by_page(max_pages=2):
    base_url = "https://www.hani.co.kr/arti?page="
    results = []
    seen = set()

    for page in range(1, max_pages + 1):
        url = base_url + str(page)
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, "html.parser")

        articles = soup.select("a.BaseArticleCard_link__Q3YFK")
        if not articles:
            break

        for article in articles:
            href = article.get("href", "")
            if not href or href in seen:
                continue
            seen.add(href)

            title_div = article.select_one("div.BaseArticleCard_title__TVFqt")
            if not title_div:
                continue
            title = title_div.text.strip()
            full_url = "https://www.hani.co.kr" + href

            image_url = get_thumbnail_from_article(full_url)
            category, created_at = get_category_and_created_at_from_article(full_url)
            content = get_content_from_article(full_url)

            results.append({
                "title": title,
                "url": full_url,
                "image": image_url,
                "category": category,
                "createdAt": created_at,
                "content": content
            })

            if len(results) >= 30:  # 크롤링할 뉴스가 30개가 넘어가면 종료
                break

        time.sleep(2)  # 서버에 부담을 주지 않기 위해 잠시 대기

    return results

if __name__ == "__main__":
    # 크롤링 실행
    # results = crawl_hani_latest_with_selenium()
    results = crawl_hani_by_page(max_pages=5)

    
    # 결과 JSON 출력 (디버깅용)
    print(json.dumps(results, ensure_ascii=False))
    
    # Spring API로 결과 전송
    send_to_spring_api(results)
