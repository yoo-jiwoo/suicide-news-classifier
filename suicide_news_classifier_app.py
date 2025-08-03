import streamlit as st
from requests_html import HTMLSession
from bs4 import BeautifulSoup
import asyncio
import nest_asyncio

# --------- 이벤트 루프 준비 (requests_html .render() 에러 방지) ---------
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
nest_asyncio.apply()

# --------- 뉴스 본문 추출 ---------
def extract_news_text(url):
    try:
        session = HTMLSession()
        r = session.get(url)
        # JS 렌더링
        r.html.render(timeout=20, sleep=2)
        html = r.html.html
        soup = BeautifulSoup(html, "html.parser")

        paragraphs = soup.find_all("p")
        text = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

        session.close()
        return text
    except Exception as e:
        return f"❌ 뉴스 본문 추출 실패: {e}"

# --------- 기사 등급 분류 ---------
def classify_article(text):
    werther_keywords = [
        "극단적 선택", "목숨을 끊", "투신", "번개탄", "유서", "스스로 목숨",
        "충격", "비극", "시신", "사망 원인", "마약 혐의", "유서 전문"
    ]
    papageno_keywords = [
        "1393", "1388", "1577-0199", "129", "1588-9191", "도움 요청", "상담",
        "정신건강", "위기 극복", "회복", "재활", "지원센터"
    ]

    risk_score = sum(word in text for word in werther_keywords)
    safe_score = sum(word in text for word in papageno_keywords)

    if risk_score >= 2 and safe_score == 0:
        return "위험"
    elif safe_score >= 2 and risk_score == 0:
        return "권장"
    else:
        return "중립"

def guideline(label):
    if label
