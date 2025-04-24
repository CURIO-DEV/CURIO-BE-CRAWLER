def crawl_joongang_articles():
    categories = {
        "정치": "politics",
        "경제": "money",
        "사회": "society",
        "국제": "world",
        "문화": "culture",
        "스포츠": "sports",
        "라이프": "lifestyle",
        "피플": "people"
    }

    base_url = "https://www.joongang.co.kr/"
    results = []

    for kor_cat, eng_cat in categories.items():
        print(f"▶️ {kor_cat} 카테고리 수집 중...")
        url = base_url + eng_cat

        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = soup.select("section.showcase_general div.card")

        for article in articles:
            title_tag = article.select_one("h2.headline a")
            image_tag = article.select_one("img")

            if not title_tag or not image_tag:
                continue

            title = title_tag.text.strip()
            article_url = title_tag.get("href")
            image_url = image_tag.get("src")

            details = get_article_details(article_url)
            if not details:
                continue

            results.append({
                "title": title,
                "url": article_url,
                "image": image_url,
                "content": details["content"],
                "category": kor_cat,
                "createdAt": details["createdAt"],
                "updatedAt": details["updatedAt"]
            })

            if len(results) >= 10:
                break

    return results
