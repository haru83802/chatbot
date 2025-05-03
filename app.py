import random
import streamlit as st
import openai
import os
import json
from dotenv import load_dotenv
from cryptography.fernet import Fernet

# .env에서 API 키 불러오기
load_dotenv()

# API 키 로드
openai_api_key = os.getenv("OPENAI_API_KEY")

# API 키가 없다면 경고 메시지 출력
if not openai_api_key:
    st.error("API 키가 설정되지 않았습니다. .env 파일을 확인해 주세요.")
    st.stop()

openai.api_key = openai_api_key

# 세션 키 생성 (암호화 키)
def generate_session_key():
    return Fernet.generate_key()

# 암호화 및 복호화 함수
def encrypt_message(message, key):
    cipher = Fernet(key)
    return cipher.encrypt(message.encode())

def decrypt_message(encrypted_message, key):
    cipher = Fernet(key)
    return cipher.decrypt(encrypted_message).decode()

# 설정
HISTORY_FILE = "chat_history.json"
MAX_MESSAGES = 20  # 오래된 메시지 제한
GPT_MODEL = "gpt-4-turbo"  # 모델 업그레이드

# 대화 저장 및 불러오기
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                encrypted_messages = json.load(f)
                decrypted_messages = [decrypt_message(msg, session_key) for msg in encrypted_messages]
                return decrypted_messages
        except Exception as e:
            st.warning(f"대화 기록을 불러오는 중 오류 발생: {e}")
    return [{"role": "system", "content": "당신은 친절한 AI 비서입니다."}]

def save_history(messages):
    try:
        encrypted_messages = [encrypt_message(msg, session_key) for msg in messages]
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(encrypted_messages, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.warning(f"대화 기록을 저장하는 중 오류 발생: {e}")

def truncate_messages(messages, max_len=MAX_MESSAGES):
    system_msg = [msg for msg in messages if msg['role'] == 'system']
    user_msgs = [msg for msg in messages if msg['role'] != 'system']
    return system_msg + user_msgs[-max_len:]

# 가짜 API 응답 생성 (예시)
def fake_api_response(messages):
    fake_responses = [
        "안녕하세요! 무엇을 도와드릴까요?",
        "저는 친절한 AI 비서입니다. 궁금한 점을 물어보세요.",
        "대화가 정말 재미있네요! 더 이야기해 주세요.",
        "오늘도 좋은 하루 되세요!",
        "GPT-4는 매우 똑똑한 모델이에요! 뭐든지 물어보세요!"
    ]
    return random.choice(fake_responses)

# 대화 요약 요청
def summarize_conversation(messages):
    summary_prompt = [
        {"role": "system", "content": "당신은 사용자의 대화를 간결하게 요약하는 요약 도우미입니다."},
        {"role": "user", "content": "다음 대화를 요약해 주세요:\n\n" + json.dumps(messages, ensure_ascii=False, indent=2)}
    ]
    try:
        response = openai.ChatCompletion.create(
            model=GPT_MODEL,
            messages=summary_prompt
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"대화 요약 중 오류 발생: {e}")
        return None

# Streamlit 인터페이스 시작
st.set_page_config(page_title="GPT-4 챗봇", page_icon="🤖")
st.title("💬 GPT-4 챗봇")
st.write("GPT-4 기반 친절한 AI 비서입니다.")

# 세션 키 생성
if "session_key" not in st.session_state:
    st.session_state.session_key = generate_session_key()
session_key = st.session_state.session_key

if "messages" not in st.session_state:
    st.session_state.messages = load_history()

# 이전 대화 출력
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("🧑‍💻 사용자").write(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message("🤖 GPT").write(msg["content"])

# 사용자 입력 처리
user_input = st.chat_input("메시지를 입력하세요...")

if user_input:
    st.chat_message("🧑‍💻 사용자").write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    try:
        trimmed = truncate_messages(st.session_state.messages)

        # 실제 OpenAI API 대신 가짜 API 사용
        reply = fake_api_response(st.session_state.messages)
        
        st.chat_message("🤖 GPT").write(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        save_history(st.session_state.messages)
    except Exception as e:
        st.error(f"GPT 오류: {e}")

# ✅ 요약 버튼
if st.button("📝 대화 요약"):
    try:
        summary = summarize_conversation(st.session_state.messages)
        if summary:
            st.success("🧠 대화 요약")
            st.markdown(summary)
    except Exception as e:
        st.error(f"요약 중 오류 발생: {e}")
