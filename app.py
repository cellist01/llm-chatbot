import streamlit as st
import requests
from datetime import datetime
import json
import pandas as pd

# 페이지 설정
st.set_page_config(
    page_title="AI 챗봇",
    page_icon="🤖",
    layout="wide"
)

# 상수 및 기본값 정의
MAX_MESSAGES = 50
API_TIMEOUT = 30
API_URL = "https://model.odyssey-ai.svc.cluster.local/v1/completions"

DEFAULT_PARAMS = {
    "max_tokens": 512,
    "temperature": 0.5,
    "top_p": 0.95,
    "presence_penalty": 0.0,
    "frequency_penalty": 0.0
}

# 스타일 설정
st.markdown("""
    <style>
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 20%;
    }
    .assistant-message {
        background-color: #f5f5f5;
        margin-right: 20%;
    }
    .message-timestamp {
        color: #666;
        font-size: 0.8rem;
    }
    .debug-info {
        background-color: #fff3e0;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

# 세션 상태 초기화
if 'messages' not in st.session_state:
    st.session_state['messages'] = []
if 'processing' not in st.session_state:
    st.session_state['processing'] = False
if 'parameters' not in st.session_state:
    st.session_state['parameters'] = DEFAULT_PARAMS.copy()

def create_prompt(user_input):
    """구조화된 프롬프트 생성"""
    return f"""아래 질문에 대해 명확하고 정확하게 답변해주세요.

질문: {user_input}

답변의 규칙:
1. 정확한 정보만 제공합니다.
2. 알지 못하는 내용은 "확실하지 않습니다"라고 답변합니다.
3. 간단명료하게 답변합니다.
4. 관련 정보만 제공합니다.

답변:"""

def call_llm_api(prompt):
    """LLM API 호출"""
    try:
        structured_prompt = create_prompt(prompt)
        
        if DEBUG_MODE:
            st.write("구조화된 프롬프트:", structured_prompt)
            st.write("현재 파라미터:", st.session_state['parameters'])
        
        response = requests.post(
            API_URL,
            json={
                "model": "model",
                "prompt": structured_prompt,
                **st.session_state['parameters']
            },
            verify=False,
            timeout=API_TIMEOUT
        )
        
        if DEBUG_MODE:
            st.write("API 응답 상태:", response.status_code)
        
        if response.status_code != 200:
            return f"API 오류: {response.status_code}"
            
        result = response.json()
        
        if DEBUG_MODE:
            st.write("API 응답:", result)
            
        if "choices" not in result or not result["choices"]:
            return "응답을 생성할 수 없습니다."
            
        return result["choices"][0]["text"].strip()
        
    except Exception as e:
        return f"Error: {str(e)}"

# 메인 화면
st.title("AI 챗봇")

# 사이드바
with st.sidebar:
    st.title("설정")
    
    # 파라미터 설정 섹션
    st.subheader("모델 파라미터")
    with st.expander("고급 설정", expanded=False):
        # max_tokens 설정
        st.session_state['parameters']['max_tokens'] = st.slider(
            "Maximum Tokens",
            min_value=50,
            max_value=1000,
            value=st.session_state['parameters'].get('max_tokens', DEFAULT_PARAMS['max_tokens']),
            step=50,
            help="생성할 최대 토큰 수 (더 긴 응답을 원할 경우 증가)"
        )

        # temperature 설정
        st.session_state['parameters']['temperature'] = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state['parameters'].get('temperature', DEFAULT_PARAMS['temperature']),
            step=0.1,
            help="높을수록 더 창의적인 응답, 낮을수록 더 일관된 응답"
        )

        # top_p 설정
        st.session_state['parameters']['top_p'] = st.slider(
            "Top P",
            min_value=0.1,
            max_value=1.0,
            value=st.session_state['parameters'].get('top_p', DEFAULT_PARAMS['top_p']),
            step=0.05,
            help="다음 토큰 선택시 고려할 확률 분포의 상위 비율"
        )

        # presence_penalty 설정
        st.session_state['parameters']['presence_penalty'] = st.slider(
            "Presence Penalty",
            min_value=-2.0,
            max_value=2.0,
            value=st.session_state['parameters'].get('presence_penalty', DEFAULT_PARAMS['presence_penalty']),
            step=0.1,
            help="새로운 주제 도입 강도 (양수: 새로운 주제 선호, 음수: 기존 주제 유지)"
        )

        # frequency_penalty 설정
        st.session_state['parameters']['frequency_penalty'] = st.slider(
            "Frequency Penalty",
            min_value=-2.0,
            max_value=2.0,
            value=st.session_state['parameters'].get('frequency_penalty', DEFAULT_PARAMS['frequency_penalty']),
            step=0.1,
            help="단어 반복 억제 정도 (양수: 반복 억제, 음수: 반복 허용)"
        )

        # 파라미터 초기화 버튼
        if st.button("파라미터 초기화"):
            st.session_state['parameters'] = DEFAULT_PARAMS.copy()
            st.experimental_rerun()

    # 프리셋 설정
    st.subheader("프리셋")
    preset = st.selectbox(
        "파라미터 프리셋",
        ["기본", "창의적", "정확성", "간단 응답", "상세 설명"],
        help="미리 정의된 파라미터 설정"
    )

    # 프리셋 선택시 파라미터 자동 설정
    if preset == "창의적":
        st.session_state['parameters'] = {
            "max_tokens": 750,
            "temperature": 0.8,
            "top_p": 0.9,
            "presence_penalty": 0.5,
            "frequency_penalty": 0.3
        }
    elif preset == "정확성":
        st.session_state['parameters'] = {
            "max_tokens": 512,
            "temperature": 0.3,
            "top_p": 0.95,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0
        }
    elif preset == "간단 응답":
        st.session_state['parameters'] = {
            "max_tokens": 128,
            "temperature": 0.4,
            "top_p": 0.95,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.5
        }
    elif preset == "상세 설명":
        st.session_state['parameters'] = {
            "max_tokens": 1000,
            "temperature": 0.6,
            "top_p": 0.9,
            "presence_penalty": 0.2,
            "frequency_penalty": 0.2
        }

    st.divider()

    # 디버그 모드 토글
    DEBUG_MODE = st.checkbox("디버그 모드", value=False)
    
    # 대화 초기화 버튼
    if st.button("대화 초기화"):
        st.session_state['messages'] = []
        st.rerun()
    
    # 대화 내보내기
    if st.session_state['messages']:
        df = pd.DataFrame(st.session_state['messages'])
        csv = df.to_csv(index=False)
        st.download_button(
            label="대화 내역 다운로드",
            data=csv,
            file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

# 채팅 이력 표시
for message in st.session_state['messages']:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        st.caption(f"{message['timestamp']}")
        if DEBUG_MODE and "debug_info" in message:
            st.info(f"디버그 정보: {message['debug_info']}")

# 사용자 입력 처리
if prompt := st.chat_input("메시지를 입력하세요..."):
    if not st.session_state['processing']:
        st.session_state['processing'] = True
        
        with st.chat_message("user"):
            st.markdown(prompt)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.caption(timestamp)
        
        message_data = {
            "role": "user",
            "content": prompt,
            "timestamp": timestamp
        }
        
        if DEBUG_MODE:
            message_data["debug_info"] = {"input_length": len(prompt)}
        
        st.session_state['messages'].append(message_data)

        with st.chat_message("assistant"):
            with st.spinner("답변 생성 중..."):
                response = call_llm_api(prompt)
                st.markdown(response)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.caption(timestamp)
        
        message_data = {
            "role": "assistant",
            "content": response,
            "timestamp": timestamp
        }
        
        if DEBUG_MODE:
            message_data["debug_info"] = {"response_length": len(response)}
        
        st.session_state['messages'].append(message_data)
        
        if len(st.session_state['messages']) > MAX_MESSAGES:
            st.session_state['messages'] = st.session_state['messages'][-MAX_MESSAGES:]
        
        st.session_state['processing'] = False
