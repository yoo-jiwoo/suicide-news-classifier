import streamlit as st
import subprocess
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# -------------------- Playwright 브라우저 설치 함수 --------------------
def install_playwright():
    """버튼 클릭 시 Playwright Chromium 설치"""
    with st.spinner("브라우저 설치 중... 잠시만 기다려주세요. (최대 1분)"):
        try:
            subprocess.run(["playwright", "install", "chromium"], check=False)
            st.success("✅ 브라우저 설치 완료! 이제 뉴스 URL을 불러올 수 있습니다.")
        except Exception as e:
            st.error(f"❌ 설치 오류: {e}")

# -------------------- 뉴스 본문 크롤링 --------------------
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

# -------------------- 기사 등급 분류 --------------------
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
    els
