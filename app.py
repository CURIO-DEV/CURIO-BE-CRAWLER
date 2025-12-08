# app.py
from fastapi import FastAPI, Request, BackgroundTasks
from news_crawler_han import crawl_hani_by_page, send_to_spring_api
import os
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from news_crawler_han import crawl_all_categories



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# 백그라운드 실행 함수
# -----------------------------
def run_crawler_task():
    news_list = crawl_hani_by_page()
    send_to_spring_api(news_list)


# -----------------------------
# POST API (Swagger 호출용)
# -----------------------------
@app.post("/curio/api/articles/crawler")
async def run_crawler(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_crawler_task)
    return {"status": "started"}


# -----------------------------
# GET 테스트용
# -----------------------------
@app.get("/run")
async def run_crawler_get(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_crawler_task)
    return {"message": "크롤링 작업이 백그라운드에서 시작되었습니다!"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}

def run_categories_task():
    data = crawl_all_categories(limit=5)
    send_to_spring_api(data)

@app.post("/curio/api/articles/crawler/categories")
async def run_categories(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_categories_task)
    return {"status": "categories started"}