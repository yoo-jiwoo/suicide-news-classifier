import streamlit as st
from newspaper import Article

# 기사 등급 분류 함수
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

# 등급별 가이드라인
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

# 뉴스 URL에서 기사 본문 추출
def extract_news_text(url):
    try:
        article = Article(url, language='ko')
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        return f"❌ 뉴스 본문 추출 실패: {e}"

# -------------------------
# 세션 상태 초기화 (에러 방지)
# -------------------------
if "article_text" not in st.session_state:
    st.session_state["article_text"] = ""

# UI 시작
st.title("📰 자살 관련 기사 자동 등급 판별기")

mode = st.radio("입력 방식 선택", ("뉴스 URL 입력", "기사 직접 입력"))

if mode == "뉴스 URL 입력":
    news_url = st.text_input("뉴스 URL을 입력하세요:")
    if st.button("URL로 기사 불러오기"):
        if news_url.strip():
            text = extract_news_text(news_url)
            if text.startswith("❌"):
                st.error(text)
            else:
                st.session_state["article_text"] = text
                st.success("기사 본문 불러오기 성공!")
        else:
            st.warning("URL을 입력하세요.")

elif mode == "기사 직접 입력":
    st.session_state["article_text"] = st.text_area("기사 본문을 입력하세요:")

# 현재 기사 본문 표시
if st.session_state["article_text"]:
    st.text_area("기사 본문", st.session_state["article_text"], height=200)

# 등급 판별 버튼
if st.button("등급 판별"):
    if st.session_state["article_text"].strip():
        label = classify_article(st.session_state["article_text"])
        st.subheader(f"등급: {label}")
        st.markdown(guideline(label))
    else:
        st.warning("기사를 입력하거나 불러오세요.")
