import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

# 중앙일보 정치 섹션 페이지 크롤링
def crawl_joongang_latest_articles():
    url = "https://www.joongang.co.kr/politics"  # 중앙일보 정치 섹션 URL
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(res.text, "html.parser")

    # 기사 목록 크롤링
    articles = soup.select("li.card")  # 각 뉴스 카드를 나타내는 <li> 태그

    print(f"Found {len(articles)} articles.")  # 디버깅용: 크롤링된 기사 수 확인

    results = []
    for article in articles:
        # 제목 (h2.headline a)
        title_element = article.select_one("h2.headline a")
        title = title_element.get_text(strip=True) if title_element else "No title"

        # 이미지 URL (figure.card_image img)
        image_element = article.select_one("figure.card_image img")
        image_url = image_element["src"] if image_element else ""

        # 내용 (p.description)
        content_element = article.select_one("p.description")
        content = content_element.get_text(strip=True) if content_element else "No content available"

        # 카테고리 (data-evnt-ctg 속성에서 추출)
        category_raw = article.select_one("a")["data-evnt-ctg"] if article.select_one("a") else ""
        category = category_raw.split("|")[1] if "|" in category_raw else category_raw

        # 기사 URL (a 태그의 href)
        article_url = title_element["href"] if title_element else ""

        # 생성시간 (date)
        date_element = article.select_one("p.date")
        created_at = date_element.get_text(strip=True) if date_element else "Unknown date"

        # 수정시간은 현재 페이지에 없으므로 일단 createdAt으로 설정
        updated_at = created_at

        article_data = {
            "title": title,
            "image": image_url,
            "content": content,
            "category": category,
            "createdAt": created_at,
            "updatedAt": updated_at,
            "sourceUrl": article_url
        }

        # 유효한 데이터만 결과 리스트에 추가
        if article_data["title"] != "No title" and article_data["content"] != "No content available":
            results.append(article_data)

        # 10개의 기사만 크롤링
        if len(results) >= 10:
            break

    return results


# Spring API로 전송
def send_to_spring_api(news_list):
    spring_url = "http://localhost:8080/curio/api/articles/crawler"  # Spring API URL
    headers = {"Content-Type": "application/json"}

    modified_list = []
    for news in news_list:
        # 제목이 "No title"이나 내용이 "No content available"인 경우는 보내지 않음
        if news["title"] == "No title" or news["content"] == "No content available":
            continue

        modified_news = {
            "title": news["title"],
            "content": news["content"],  
            "summaryShort": "",  
            "summaryMedium": "",
            "summaryLong": "",  
            "category": news["category"],
            "likeCount": 0,  
            "imageUrl": news["image"],
            "sourceUrl": news["sourceUrl"],  # 수정된 부분
            "createdAt": news["createdAt"],
            "updatedAt": news["updatedAt"]
        }
        modified_list.append(modified_news)

    response = requests.post(spring_url, json=modified_list, headers=headers)

    if response.status_code == 200:
        print("Data successfully sent to Spring API")
    else:
        print(f"Failed to send data: {response.status_code}, {response.text}")


# 크롤링 실행 함수
def main():
    results = crawl_joongang_latest_articles()

    # 결과 출력 (디버깅용)
    if results:
        print(json.dumps(results, ensure_ascii=False, indent=4))
    else:
        print("No valid articles found.")

    # Spring API로 결과 전송 (API URL을 수정할 수 있음)
    send_to_spring_api(results)

# 메인 실행
if __name__ == "__main__":
    main()
