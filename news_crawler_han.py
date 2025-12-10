import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import json

# --------------------------------------------
# 카테고리 URL 매핑
# --------------------------------------------
CATEGORY_URLS = {
    "스포츠": "https://www.hani.co.kr/arti/sports/sports_general",
    "국제": "https://www.hani.co.kr/arti/international/international_general",
    "정치": "https://www.hani.co.kr/arti/politics/politics_general",
    "외교": "https://www.hani.co.kr/arti/politics/diplomacy",
    "사회": "https://www.hani.co.kr/arti/society/society_general",

    "연예": "https://www.hani.co.kr/arti/culture/entertainment",
    "환경": "https://www.hani.co.kr/arti/society/environment",
    "경제": "https://www.hani.co.kr/arti/economy/economy_general",
    "부동산": "https://www.hani.co.kr/arti/economy/property",
    "자동차": "https://www.hani.co.kr/arti/economy/car",

    "여행": "https://www.hani.co.kr/arti/culture/travel",
    "과학": "https://www.hani.co.kr/arti/science/science_general",
    "건강": "https://www.hani.co.kr/arti/hanihealth/healthlife",

    "법률": "https://www.hani.co.kr/arti/politics/administration",
    "교육": "https://www.hani.co.kr/arti/society/schooling",
    "종교": "https://www.hani.co.kr/arti/society/religious",
    "IT": "https://www.hani.co.kr/arti/economy/it",
    "생활": "https://www.hani.co.kr/arti/society/life"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://www.google.com",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}

# --------------------------------------------
# 1) 썸네일 URL 가져오기
# --------------------------------------------
def get_thumbnail_from_article(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(res.text, 'html.parser')
        og_image = soup.select_one("meta[property='og:image']")
        if og_image:
            return og_image.get("content")
    except:
        pass
    return None


# --------------------------------------------
# 2) 카테고리 + 등록시간 가져오기
# --------------------------------------------
def get_category_and_created_at_from_article(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(res.text, 'html.parser')

        breadcrumb = soup.select_one("div.ArticleDetailView_breadcrumb___UwRC")
        category = breadcrumb.find("a").get_text(strip=True) if breadcrumb else ""

        created_at = ""
        for li in soup.select("ul.ArticleDetailView_dateList__tniXJ li"):
            if "등록" in li.text:
                span = li.find("span")
                if span:
                    created_at = span.text.strip()
                break

        return category, created_at
    except:
        return "", ""


# --------------------------------------------
# 3) 본문 가져오기
# --------------------------------------------
def get_content_from_article(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(res.text, 'html.parser')
        content = "\n".join(p.get_text(strip=True) for p in soup.select("p.text"))
        return content
    except:
        return ""


# --------------------------------------------
# 날짜 포맷팅
# --------------------------------------------
def format_datetime(korean_time_str):
    try:
        dt = datetime.strptime(korean_time_str, "%Y-%m-%d %H:%M")
        return dt.isoformat()
    except:
        return "2025-04-19T00:00:00"


# --------------------------------------------
# 최신 기사 크롤링 (arti?page=1~N)
# --------------------------------------------
def crawl_hani_by_page(max_pages=5):
    base_url = "https://www.hani.co.kr/arti?page="
    results = []
    seen = set()

    for page in range(1, max_pages + 1):
        url = base_url + str(page)
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")

        articles = soup.select("a.BaseArticleCard_link__Q3YFK")
        if not articles:
            continue

        for article in articles:
            href = article.get("href")
            if not href or href in seen:
                continue

            seen.add(href)
            title_div = article.select_one("div.BaseArticleCard_title__TVFqt")
            if not title_div:
                continue

            full_url = "https://www.hani.co.kr" + href
            title = title_div.text.strip()
            image = get_thumbnail_from_article(full_url)
            category, created_at = get_category_and_created_at_from_article(full_url)
            content = get_content_from_article(full_url)

            results.append({
                "title": title,
                "url": full_url,
                "image": image,
                "category": category,
                "createdAt": created_at,
                "content": content
            })

            if len(results) >= 30:
                return results

        time.sleep(1)

    return results


# --------------------------------------------
# 카테고리 1개 크롤링
# --------------------------------------------
def crawl_category_once(category_name, limit=5):
    url = CATEGORY_URLS.get(category_name)
    if not url:
        return []

    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    articles = soup.select("a.BaseArticleCard_link__Q3YFK")
    results = []

    for tag in articles[:limit]:
        href = tag.get("href")
        if not href:
            continue

        title_tag = tag.select_one("div.BaseArticleCard_title__TVFqt")
        if not title_tag:
            continue

        full_url = "https://www.hani.co.kr" + href
        title = title_tag.text.strip()
        image = get_thumbnail_from_article(full_url)
        _, created_at = get_category_and_created_at_from_article(full_url)
        content = get_content_from_article(full_url)

        results.append({
            "title": title,
            "url": full_url,
            "image": image,
            "category": category_name,  # 매칭된 카테고리 이름
            "createdAt": created_at,
            "content": content
        })

    return results


# --------------------------------------------
# 20개 카테고리 전체 크롤링
# --------------------------------------------
def crawl_all_categories(limit=5):
    all_results = []
    for category in CATEGORY_URLS.keys():
        print(f"[INFO] Crawling category: {category}")
        data = crawl_category_once(category, limit)
        all_results.extend(data)
        time.sleep(1)
    return all_results


# --------------------------------------------
# 스프링 서버로 전송
# --------------------------------------------
def send_to_spring_api(news_list):
    spring_url = "https://api.curi-o.site/curio/api/articles/crawler"
    headers = {"Content-Type": "application/json"}

    modified = []
    for news in news_list:
        created_at = news.get("createdAt") or "2025-04-19 12:00"
        formatted = format_datetime(created_at)

        modified.append({
            "title": news["title"],
            "content": news["content"],
            "summaryShort": "",
            "summaryMedium": "",
            "summaryLong": "",
            "category": news["category"],
            "likeCount": 0,
            "imageUrl": news["image"],
            "sourceUrl": news["url"],
            "createdAt": formatted,
            "updatedAt": formatted
        })

    response = requests.post(spring_url, json=modified, headers=headers)
    print("SPRING RESPONSE:", response.status_code)


