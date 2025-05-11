import requests
from bs4 import BeautifulSoup

CATEGORIES = [
    "politics", "money", "society", "world", 
    "culture", "sports", "lifestyle", "people"
]

API_ENDPOINT = "http://localhost:8080/api/articels/crawler"  # 한겨레 때와 같은 엔드포인트

def crawl_joongang_articles(category="politics"):
    url = f"https://www.joongang.co.kr/{category}"
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(res.text, "html.parser")

    articles = soup.select("ul#story_list li.card")
    results = []

    for article in articles:
        try:
            link_tag = article.select_one("h2.headline a")
            title = link_tag.text.strip()
            article_url = link_tag["href"]
            description = article.select_one("p.description").text.strip()
            date = article.select_one("p.date").text.strip()
            image_tag = article.select_one("figure.card_image img")
            image_url = image_tag["src"] if image_tag else None

            article_data = {
                "title": title,
                "url": article_url,
                "content": description,
                "category": category,
                "media": "중앙일보",
                "publishedAt": date,
                "thumbnail": image_url
            }

            # POST 요청으로 전송
            response = requests.post(API_ENDPOINT, json=article_data)
            if response.status_code == 200:
                print(f"[성공] {title}")
            else:
                print(f"[실패] {title} - Status: {response.status_code}")

            results.append(article_data)
        except Exception as e:
            print(f"[ERROR] {e}")
            continue

    return results

def crawl_all_categories_and_send():
    for category in CATEGORIES:
        print(f"[{category.upper()}] 크롤링 중...")
        crawl_joongang_articles(category)

if __name__ == "__main__":
    crawl_all_categories_and_send()
