import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil.parser import parse
import time
import json


# -----------------------------------------------------
# 1) 썸네일 URL 가져오기 (기존 동일)
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
# 2) 카테고리 + 등록일 가져오기 (기존 동일)
# -----------------------------------------------------
def get_category_and_created_at_from_article(url):
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, 'html.parser')

        # 기존 로직 유지
        breadcrumb = soup.select_one("div.ArticleDetailView_breadcrumb___UwRC")
        category = ""
        if breadcrumb:
            first_category = breadcrumb.find("a")
            if first_category:
                category = first_category.get_text(strip=True)

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


# -----------------------------------------------------
# 3) 기사 본문 가져오기 (기존 동일)
# -----------------------------------------------------
def get_content_from_article(url):
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.select("p.text")
        content = "\n".join(p.get_text(strip=True) for p in paragraphs)
        return content
    except Exception as e:
        print(f"[ERROR] Failed to fetch content from {url} - {e}")
        return ""


# -----------------------------------------------------
# 4) 날짜 포맷팅 (기존 유지)
# -----------------------------------------------------
def format_datetime(korean_time_str):
    try:
        dt = datetime.strptime(korean_time_str, "%Y-%m-%d %H:%M")
        return dt.isoformat()
    except Exception:
        return "2025-04-19T00:00:00"


# -----------------------------------------------------
# 5) 원래 Selenium으로 했던 최신기사 크롤링 → requests 기반으로 재구현
# 구조는 그대로 유지, 내부만 대체
# -----------------------------------------------------
def crawl_hani_latest_with_selenium():
    """
    기존 함수 이름을 유지하지만 내부는 Selenium 없이 동작
    """

    url = "https://www.hani.co.kr/arti"
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(res.text, "html.parser")

    articles = soup.select("a.BaseArticleCard_link__Q3YFK")

    results = []
    seen = set()

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
            break

    return results


# -----------------------------------------------------
# 6) 페이지 기반 크롤링 (기존 동일, 내부 안정화)
# -----------------------------------------------------
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
                break

        time.sleep(1)

    return results


# -----------------------------------------------------
# 7) Spring API 전송 (기존과 완전히 동일)
# -----------------------------------------------------
def send_to_spring_api(news_list):
    spring_url = "https://api.curi-o.site/curio/api/articles/crawler"
    headers = {"Content-Type": "application/json"}

    modified_list = []
    for news in news_list:
        created_at = news.get("createdAt", "")
        if not created_at:
            created_at = "2025-04-19 12:00"

        formatted_date = format_datetime(created_at)

        modified_news = {
            "title": news["title"],
            "content": news["content"],
            "summaryShort": "",
            "summaryMedium": "",
            "summaryLong": "",
            "category": news.get("category", ""),
            "likeCount": 0,
            "imageUrl": news["image"],
            "sourceUrl": news["url"],
            "createdAt": formatted_date,
            "updatedAt": formatted_date
        }
        modified_list.append(modified_news)

    response = requests.post(spring_url, json=modified_list, headers=headers)

    print("SPRING RESPONSE:", response.status_code, response.text)


# -----------------------------------------------------
# 실행
# -----------------------------------------------------
if __name__ == "__main__":
    # 원래는 Selenium 기반이었지만 동작 동일
    # results = crawl_hani_latest_with_selenium()
    results = crawl_hani_by_page(max_pages=5)

    print(json.dumps(results, ensure_ascii=False))
    send_to_spring_api(results)
