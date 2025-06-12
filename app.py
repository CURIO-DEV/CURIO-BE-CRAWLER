# app.py
from fastapi import FastAPI, Request
from news_crawler_han import crawl_hani_by_page, send_to_spring_api
import os
import uvicorn

# CORS 미들웨어 임포트
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS 미들웨어 추가 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # 모든 오리진 허용 (배포시 필요한 경우 도메인 제한 가능)
    allow_credentials=True,
    allow_methods=["*"],       # 모든 HTTP 메서드 허용
    allow_headers=["*"],       # 모든 헤더 허용
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)


@app.post("/curio/api/articles/crawler")
async def run_crawler(request: Request):
    try:
        news_list = crawl_hani_by_page()
        send_to_spring_api(news_list)
        return {"status": "success", "count": len(news_list)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/run")
def run_crawler():
    news_list = crawl_hani_by_page()
    send_to_spring_api(news_list)
    return {"message": "크롤링 및 전송 완료!"}
