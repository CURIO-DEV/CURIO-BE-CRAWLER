import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from datetime import datetime
from dateutil.parser import parse
import time
import json


# -----------------------------------------------------
# 0) Headless Chrome Driver 생성
# -----------------------------------------------------
def get_driver():
    chrome_options = Options()
    chrome_options.binary_location = "/usr/bin/google-chrome"
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service("/usr/bin/chromedriver")

    driver = webdriver.Chrome(
        service=service,
        options=chrome_options
    )
    return driver


# -----------------------------------------------------
# 1) 썸네일 가져오기
# -----------------------------------------------------
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


# -----------------------------------------------------
# 2) 카테고리 + 날짜 가져오기
# -----------------------------------------------------
def get_category_and_created_at_from_article(url):
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, 'html.parser')

        # 카테고리
        category_tag = soup.select_one("div.article-category a")
        category = category_tag.get_text(strip=True) if category_tag else ""

        # 날짜
        created_at = ""
        date_tag = soup.select_one("span.date")
        if date_tag:
            try:
                created_at = parse(date_tag.get_text(strip=True)).strftime("%Y-%m-%d %H:%M")
            except:
                created_at = ""

        return category, created_at
    except Exception as e:
        print(f"카테고리/시간 가져오기 실패: {e}")
        return "", ""


# -----------------------------------------------------
# 3) 본문 가져오기
# -----------------------------------------------------
def get_content_from_article(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        content_div = soup.select_one("#article-view-content-div")
        if not content_div:
            return ""

        paragraphs = content_div.find_all("p")
        content = "\n".join(p.get_text(strip=True) for p in paragraphs)

        return content
    except Exception as e:
        print(f"[ERROR] 본문 가져오기 실패 {url} - {e}")
        return ""


# -----------------------------------------------------
# 4) 날짜 포맷 통일
# -----------------------------------------------------
def format_datetime(korean_time_str):
    try:
        return parse(korean_time_str).isoformat()
    except:
        return datetime.now().isoformat()


# -----------------------------------------------------
# 5) 페이지 크롤링 (Selenium)
# -----------------------------------------------------
def crawl_hani_by_page(max_pages=2):
    base_url = "https://www.hani.co.kr/arti?page="
    results = []
    seen = set()

    driver = get_driver()

    for page in range(1, max_pages + 1):
        url = base_url + str(page)
        print(f"\n=== [PAGE] {url} ===")

        driver.get(url)
        time.sleep(2)

        html = driver.page_source

        print("===== DEBUG PAGE HTML =====")
        print(html[:2000])
        print("===== END DEBUG =====")

        soup = BeautifulSoup(html, "html.parser")

        # 모든 기사 링크 (CSS module 무시)
        article_links = soup.select("a[href*='/arti/']")

        for tag in article_links:
            href = tag.get("href", "")
            if not href or href in seen:
                continue
            seen.add(href)

            full_url = "https://www.hani.co.kr" + href

            # 제목
            title_tag = tag.select_one("h4, strong, span")
            title = title_tag.get_text(strip=True) if title_tag else ""
            if not title:
                continue

            print(f"[기사 발견] {title}")

            # 상세 크롤링
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

            if len(results) >= 30:
                driver.quit()
                return results

        time.sleep(1)

    driver.quit()
    return results


# -----------------------------------------------------
# 6) Spring 서버 전송
# -----------------------------------------------------
def send_to_spring_api(news_list):
    spring_url = "https://api.curi-o.site/curio/api/articles/crawler"
    headers = {"Content-Type": "application/json"}

    formatted = []
    for news in news_list:
        created_at = news.get("createdAt") or datetime.now().isoformat()

        formatted.append({
            "title": news["title"],
            "content": news["content"],
            "summaryShort": "",
            "summaryMedium": "",
            "summaryLong": "",
            "category": news.get("category", ""),
            "likeCount": 0,
            "imageUrl": news["image"],
            "sourceUrl": news["url"],
            "createdAt": format_datetime(created_at),
            "updatedAt": format_datetime(created_at)
        })

    response = requests.post(spring_url, json=formatted, headers=headers)
    print("SPRING RESPONSE:", response.status_code, response.text)


# -----------------------------------------------------
# 실행 테스트
# -----------------------------------------------------
if __name__ == "__main__":
    results = crawl_hani_by_page(max_pages=5)
    print(json.dumps(results, ensure_ascii=False))
    send_to_spring_api(results)
