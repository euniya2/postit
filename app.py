import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import base64
from PIL import Image
import io

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="코딩 결과물 공유 게시판", layout="wide")

st.markdown("""
    <style>
    .postit-card {
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        box-shadow: 5px 5px 15px rgba(0,0,0,0.1);
        color: #333;
        min-height: 200px;
        transition: transform 0.2s;
    }
    .postit-card:hover {
        transform: scale(1.02);
    }
    </style>
""", unsafe_allow_html=True)

# 2. Google Sheets 연결
url = st.secrets["gsheets_url"]
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    return conn.read(spreadsheet=url, usecols=[0,1,2,3,4,5], ttl="0s")

# 3. 이미지 처리 함수 (Base64 변환)
def img_to_base64(image_file):
    if image_file is not None:
        img = Image.open(image_file)
        # 용량 최적화 (썸네일 크기)
        img.thumbnail((400, 400))
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    return ""

# 4. 사이드바: 입력 폼
with st.sidebar:
    st.header("📝 새 포스트잇 작성")
    with st.form(key="postit_form", clear_on_submit=True):
        name = st.text_input("이름", placeholder="익명")
        content = st.text_area("내용 (코드 링크, 소감 등)", placeholder="여기에 내용을 입력하거나 링크를 붙여넣으세요.")
        
        col1, col2 = st.columns(2)
        with col1:
            emoji = st.selectbox("이모지", ["😊", "💻", "🚀", "💡", "🔥", "✅", "🎉", "🌈"])
        with col2:
            color = st.color_picker("색상", "#FFF176") # 기본 노란색
            
        uploaded_file = st.file_uploader("이미지 첨부", type=['png', 'jpg', 'jpeg'])
        
        submit_button = st.form_submit_button(label="게시판에 올리기")

    if submit_button:
        if content:
            # 새로운 데이터 행 생성
            new_img_data = img_to_base64(uploaded_file)
            new_data = pd.DataFrame([{
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "name": name if name else "익명",
                "content": content,
                "emoji": emoji,
                "color": color,
                "image": new_img_data
            }])
            
            # 기존 데이터 읽기 및 추가
            existing_data = load_data()
            updated_df = pd.concat([existing_data, new_data], ignore_index=True)
            
            # 구글 시트 업데이트
            conn.update(spreadsheet=url, data=updated_df)
            st.success("게시물이 성공적으로 등록되었습니다!")
            st.rerun()
        else:
            st.error("내용을 입력해주세요!")

# 5. 메인 화면: 게시판 레이아웃
st.title("📌 실시간 코딩 공유 게시판")
st.info("우측 사이드바에서 글을 쓰고 친구들의 코드를 확인해 보세요!")

df = load_data()

# 최신글이 위로 오게 정렬
if not df.empty:
    df = df.iloc[::-1]

# 그리드 레이아웃 설정 (3열)
cols = st.columns(3)

for i, row in df.iterrows():
    with cols[i % 3]:
        # 이미지 HTML 처리
        img_html = f'<img src="data:image/png;base64,{row["image"]}" style="width:100%; border-radius:10px; margin-top:10px;">' if row["image"] else ""
        
        # 포스트잇 카드 렌더링
        st.markdown(
            f"""
            <div class="postit-card" style="background-color:{row['color']};">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:1.5rem;">{row['emoji']}</span>
                    <span style="font-size:0.8rem; opacity:0.7;">{row['date']}</span>
                </div>
                <h4 style="margin: 10px 0;">{row['name']}</h4>
                <div style="white-space: pre-wrap; word-break: break-all;">{row['content']}</div>
                {img_html}
            </div>
            """, 
            unsafe_allow_html=True
        )
