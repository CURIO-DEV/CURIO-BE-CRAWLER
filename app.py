# app.py
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from news_crawler_han import (
    crawl_hani_by_page,
    crawl_all_categories,
    send_to_spring_api
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# 최신기사 크롤링 작업
# --------------------------------------------------
def run_crawler_task():
    print("🔍 최신 기사 크롤링 시작")
    news_list = crawl_hani_by_page(max_pages=5)
    print("📦 최신 기사 개수:", len(news_list))

    if not news_list:
        print("⚠ 최신 기사 크롤링 결과가 0개입니다.")
    else:
        print("📤 스프링 서버로 전송 시작")

    send_to_spring_api(news_list)
    print("✅ 최신 기사 전송 완료")


# --------------------------------------------------
# 20개 카테고리 크롤링 작업
# --------------------------------------------------
def run_categories_task():
    print("🔍 카테고리 전체 크롤링 시작")
    data = crawl_all_categories(limit=5)

    print("📦 전체 카테고리 기사 수:", len(data))
    for item in data:
        print(f"- {item['category']} / {item['title']}")

    if not data:
        print("⚠ 카테고리 크롤링 결과 없음")

    print("📤 스프링 서버로 전송 시작")
    send_to_spring_api(data)
    print("✅ 카테고리 기사 전송 완료")


# --------------------------------------------------
# 최신기사 실행 API
# --------------------------------------------------
@app.post("/curio/api/articles/crawler")
async def run_latest(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_crawler_task)
    return {"status": "latest started"}


# --------------------------------------------------
# 카테고리 전체 실행 API
# --------------------------------------------------
@app.post("/curio/api/articles/crawler/categories")
async def run_categories(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_categories_task)
    return {"status": "categories started"}


# --------------------------------------------------
# 헬스 체크
# --------------------------------------------------
@app.get("/health")
async def health_check():
    return {"status": "ok"}
