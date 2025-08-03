import streamlit as st
from requests_html import HTMLSession
from bs4 import BeautifulSoup
import asyncio
import nest_asyncio
import os, requests
import re
from bs4 import BeautifulSoup


# --------- 이벤트 루프 준비 (requests_html .render() 에러 방지) ---------
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
nest_asyncio.apply()

# --------- 뉴스 본문 추출 ---------
def extract_news_text(url, max_retry=3):
    api_key = st.secrets["SCRAPINGANT_KEY"]
    api_url = (
        "https://api.scrapingant.com/v2/general?url="
        + requests.utils.quote(url)
        + f"&x-api-key={api_key}&browser=true&render_js=true"
    )
    for attempt in range(1, max_retry + 1):
        try:
            resp = requests.get(api_url, timeout=60)   # ← 60초로 증가
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            paragraphs = soup.find_all("p")
            text = "\n".join(
                p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)
            )
            return text or "❌ 기사 본문을 찾지 못했습니다."
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            if attempt == max_retry:
                return "❌ 본문 추출 실패: ScrapingAnt 응답 지연"
            time.sleep(2)  # 2초 후 재시도
        except Exception as e:
            return f"❌ 본문 추출 실패: {e}"

# --------- 기사 등급 분류 ---------
def normalize(text):
    # 숫자·한글·영문만 남기고 전부 제거 → 공백 하나로
    cleaned = re.sub(r"[^0-9가-힣a-zA-Z]", " ", text)
    return re.sub(r"\s+", " ", cleaned)
    
# ─── 새 함수 추가 ───
HELP_PATTERNS = [
    r"1393",
    r"1388",
    r"1577[-\s]?0199",
    r"1588[-\s]?9191",
    r"\b129\b"
]
def has_help_line(text: str) -> bool:
    for pat in HELP_PATTERNS:
        if re.search(pat, text):
            return True
    return False
# ───────────────────

import re

# ───────────────────────── ① 도움 경로 정규식 ─────────────────────────
HELP_PATTERNS = [
    r"1393",
    r"1388",
    r"1577[-\s]?0199",
    r"1588[-\s]?9191",
    r"\b129\b",
]

def has_help_line(text: str) -> bool:
    """1393·1388·1577-0199·1588-9191·129 등 ‘핫라인’ 표기 탐지"""
    for pat in HELP_PATTERNS:
        if re.search(pat, text):
            return True
    return False
# ──────────────────────────────────────────────────────────────────────


def classify_article(text: str) -> str:
    werther_keywords = [
        "극단적 선택", "목숨을 끊", "투신", "번개탄", "유서", "스스로 목숨",
        "충격", "비극", "시신", "사망 원인", "마약 혐의", "유서 전문"
    ]

    # ② 위험 점수 : 키워드가 몇 개 들어 있는가
    risk_score = sum(k in text for k in werther_keywords)

    # ③ 안전 점수 : 핫라인 하나라도 발견되면 1
    safe_score = 1 if has_help_line(text) else 0

    # ④ 분류 규칙 (도움 번호 하나만 있어도 ‘권장’으로 인정)
    if risk_score >= 2 and safe_score == 0:
        return "위험"
    elif safe_score >= 1 and risk_score == 0:
        return "권장"
    else:
        return "중립"

# --------- 등급별 가이드라인 ---------
def guideline(label):
    if label == "위험":
        return """⚠️ **위험(베르테르형)**  
- 방법·도구·장소·유서 내용 언급  
- 자극적·선정적 헤드라인  
- 사건 원인 단순 귀속(개인 책임 프레임)  
- 도움 경로(1393, 1388 등) 누락  
**→ 자살 보도 준칙 4.0에 따라 전면 수정 필요**"""
    elif label == "중립":
        return """ℹ️ **중립**  
- 보도 준칙 대체로 준수하나 회복 서사·예방 정보 부족  
- 방법·장소·유서 비공개, 그러나 도움 경로 없음  
- 구조적 원인·정책 대안 부족  
**→ 도움 경로와 회복 서사 추가 필요**"""
    elif label == "권장":
        return """✅ **권장(파파게노형)**  
- 방법·도구·장소·유서 내용 전면 비공개  
- 중립적·사실적 표현 사용  
- 회복 사례·구조적 원인 제시  
- 도움 경로(1393, 1577-0199, 1388 등) 필수 삽입  
**→ 예방 효과가 높은 모범 보도 사례**"""
    return ""

# --------- Streamlit UI ---------
if "article_text" not in st.session_state:
    st.session_state.article_text = ""

st.title("📰 자살 관련 기사 자동 등급 판별기")

mode = st.radio("입력 방식 선택", ("뉴스 URL 입력", "기사 직접 입력"))

if mode == "뉴스 URL 입력":
    news_url = st.text_input("뉴스 URL을 입력하세요:")

    if st.button("URL로 기사 불러오기"):
        if news_url.strip():
            text = extract_news_text(news_url)
            if len(text) < 50:
                st.error("❌ 기사를 불러오지 못했습니다. (URL 확인)")
            else:
                st.session_state.article_text = text
                st.success("기사 본문 불러오기 성공!")
        else:
            st.warning("URL을 입력하세요.")
elif mode == "기사 직접 입력":
    st.session_state.article_text = st.text_area("기사 본문을 입력하세요:")

# 현재 기사 본문 표시
if st.session_state.article_text:
    st.text_area("기사 본문", st.session_state.article_text, height=200)

# 등급 판별 버튼
if st.button("등급 판별"):
    if st.session_state.article_text.strip():
        label = classify_article(st.session_state.article_text)
        st.subheader(f"등급: {label}")
        st.markdown(guideline(label))
    else:
        st.warning("기사를 입력하거나 불러오세요.")









