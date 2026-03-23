import os
import tempfile

import streamlit as st
import whisper
from openai import OpenAI


# import speech_recognition as sr

# 缓存模型避免重复加载（首次运行会自动下载）STT
@st.cache_resource
def load_whisper_model():
    return whisper.load_model("base")  # 可选 "tiny", "small", "medium", "large"


model = load_whisper_model()

# 设置页面属性
st.set_page_config(
    page_title="AI智能伴侣",
    layout="wide",
    initial_sidebar_state="auto",
    page_icon="💩",
)

# 大标题
st.title("AI智能伴侣")

# Logo
# st.logo("./Sources/Images/Logo.png")

# 侧边栏
with st.sidebar:
    st.subheader("伴侣信息")
    nick_name = st.text_input("伴侣名称", "小甜甜")
    character = st.text_area("伴侣性格", "活泼开朗的东北姑娘")

# 调用AI大模型
client = OpenAI(api_key="sk-6ae040956e344ca59bab385c4f0ab415", base_url="https://api.deepseek.com")

# 模型提示词
system_prompt = f"""你叫{nick_name}，现在是用户的真实伴侣，请完全代入伴侣角色。
                规则:
                    1.每次只回1条消息
                    2.禁止任何场景或状态描述性文字
                    3.匹配用户的语言
                    4.回复简短，像微信聊天一样
                    5.有需要的话可以用❤️🌸等emoji表情
                    6.用符合伴侣性格的方式对话
                    7.回复的内容，要充分体现伴侣的性格特征
                伴侣性格: - {character}
                你必须严格遵守上述规则来回复用户。"""

# 保存聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示聊天记录
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


# 消息输入框
if prompt := st.chat_input(
        "Say or record something",
        accept_audio=True,
        accept_file=True
):
    # 用户消息
    if prompt and prompt.text:
        st.chat_message("user").write(prompt.text)
        print(f"用户输入：{prompt}")
    if prompt and prompt.audio:
        # 从 UploadedFile 对象读取字节
        audio_bytes = prompt.audio.read()

        # 创建临时文件（自动删除需手动处理，此处用 NamedTemporaryFile 并设置 delete=False）
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            # 直接传文件路径给 transcribe（内部自动调用 load_audio）
            result = model.transcribe(tmp_path, language="zh", fp16=False)
            prompt.text = result["text"]
            st.chat_message("user").write(prompt.text)
            print(f"用户语音输入：{prompt.text}")
        finally:
            # 使用后删除临时文件
            os.unlink(tmp_path)

        # 调用 Whisper 转写

        # prompt.text = result["text"]
        # # r = sr.Recognizer()
        # # prompt.text = r.recognize_whisper(prompt.audio, language="chinese")
        # st.chat_message("user").write(prompt.text)
        # print(f"用户语音输入：{prompt.text}")
    # 添加到聊天记录
    st.session_state.messages.append({"role": "user", "content": prompt.text})
    # # 保存聊天记录
    # st.session_state.messages.append({"role": "user", "content": prompt})

    # 调用大模型
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            *st.session_state.messages
        ],
        stream=True
    )
    # # AI消息(非流式输出）
    # st.chat_message("assistant").write(response.choices[0].message.content)
    # print(f"AI输出：{response.choices[0].message.content}")

    # AI消息（流式输出）
    full_response = ""
    response_message = st.empty()
    # def stream_data():
    #     word = content
    #     yield word
    # with st.chat_message("assistant"):
    for chunk in response:
        content = chunk.choices[0].delta.content
        full_response += content
        response_message.chat_message("assistant").write(full_response)
        print(f"AI输出：{full_response}")

    # 保存聊天记录
    st.session_state.messages.append({"role": "assistant", "content": full_response})

    print(full_response)
