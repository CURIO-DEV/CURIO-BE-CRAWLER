import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import json

# 중앙일보 정치 섹션 페이지 크롤링
def crawl_joongang_latest_articles():
    url = "https://www.joongang.co.kr/article/section/politics"  # 중앙일보 정치 섹션 URL
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(res.text, "html.parser")

    # 기사 목록 크롤링
    articles = soup.select("section.showcase_general .card a.img_thumbnail")

    results = []
    seen = set()  # 중복된 링크 방지용
    for article in articles:
        href = article.get("href", "")
        if href in seen or not href:
            continue
        seen.add(href)

        full_url = "https://www.joongang.co.kr" + href

        # 각 기사에서 필요한 정보 크롤링
        article_data = parse_joongang_article(full_url)
        if article_data:
            results.append(article_data)

        # 10개의 기사만 크롤링
        if len(results) >= 10:
            break

    return results

# 중앙일보 기사에서 필요한 정보 파싱
def parse_joongang_article(url):
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, "html.parser")

        # 제목
        title = soup.select_one("h2.headline.fs_lg32 > a").get_text(strip=True)

        # 이미지 URL
        image_url = soup.select_one("figure.card_image img")["src"]

        # 내용
        content = soup.select_one("p.description").get_text(strip=True)

        # 카테고리
        category_raw = soup.select_one("h2.headline.fs_lg32 > a").get("data-evnt-ctg", "")
        category = category_raw.split("|")[1] if "|" in category_raw else ""

        # 생성시간
        created_at = soup.select_one("time[itemprop='datePublished']")["datetime"]

        # 수정시간
        updated_at = soup.select_one("time[itemprop='dateModified']")["datetime"]

        return {
            "title": title,
            "image": image_url,
            "content": content,
            "category": category,
            "createdAt": created_at,
            "updatedAt": updated_at,
        }

    except Exception as e:
        print(f"중앙일보 기사 파싱 실패: {e}")
        return {}

# 크롤링 실행 함수
def main():
    results = crawl_joongang_latest_articles()

    # 결과 출력 (디버깅용)
    print(json.dumps(results, ensure_ascii=False))

    # Spring API로 결과 전송 (API URL을 수정할 수 있음)
    send_to_spring_api(results)

# Spring API로 전송
def send_to_spring_api(news_list):
    spring_url = "http://localhost:8080/curio/article/crawler"  # Spring API URL
    headers = {"Content-Type": "application/json"}

    modified_list = []
    for news in news_list:
        modified_news = {
            "title": news["title"],
            "content": news["content"],  
            "summaryShort": "",  
            "summaryMedium": "",
            "summaryLong": "",  
            "category": news["category"],
            "likeCount": 0,  
            "imageUrl": news["image"],
            "sourceUrl": url,
            "createdAt": news["createdAt"],
            "updatedAt": news["updatedAt"]
        }
        modified_list.append(modified_news)

    response = requests.post(spring_url, json=modified_list, headers=headers)

    if response.status_code == 200:
        print("Data successfully sent to Spring API")
    else:
        print(f"Failed to send data: {response.status_code}, {response.text}")

if __name__ == "__main__":
    main()
