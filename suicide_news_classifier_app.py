import streamlit as st
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import subprocess
import os

# -------------------- Playwright 설치 자동 실행 --------------------
def ensure_playwright_installed():
    """Cloud 환경에서 playwright와 chromium을 자동 설치"""
    try:
        import playwright
        # chromium이 설치되어 있는지 확인
        chromium_path = os.path.expanduser("~/.cache/ms-playwright/chromium")
        if not os.path.exists(chromium_path):
            st.info("🔄 Playwright Chromium 설치 중...")
            subprocess.run(["playwright", "install", "chromium"], check=True)
    except ImportError:
        st.info("🔄 Playwright 설치 중...")
        subprocess.run(["pip", "install", "playwright"], check=True)
        subprocess.run(["playwright", "install", "chromium"], check=True)

# -------------------- 기사 크롤링 --------------------
def extract_news_text_playwright(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=60000)
            page.wait_for_timeout(3000)  # JS 로딩 대기
            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, "html.parser")
        paragraphs = soup.find_all("p")
        text = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        return text
    except Exception as e:
        return f"❌ 뉴스 본문 추출 실패: {e}"

# -------------------- 등급 분류 --------------------
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
    if label == "위험":
        return """⚠️ **위험(베르테르형)**  
- 방법·도구·장소·유서 내용 언급  
- 자극적·선정적 헤드라인  
- 사건 원인 단순 귀속(개인 책임 프레임)  
- 도움 경로(1393, 1388 등) 누락  
**→ 자살 보도 준칙 4.0에 따라 전면 수정 필요**"""
    elif label == "중립":
        return
