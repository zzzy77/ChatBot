import json
import os
import tempfile
# import re
import streamlit as st
import whisper
from openai import OpenAI
from datetime import datetime
import asyncio


# ==================== 配置管理 ====================
class Config:
    """应用配置"""
    PAGE_TITLE = "ChatBot"
    PAGE_ICON = "💩"
    WHISPER_MODEL = "base"  # 可选："tiny", "small", "medium", "large"
    DEEPSEEK_API_KEY = "sk-83f291ef370149b5b56719b27b4315d0"
    DEEPSEEK_BASE_URL = "https://api.deepseek.com"
    DEEPSEEK_MODEL = "deepseek-chat"
    DEFAULT_NICKNAME = "张淑云"
    DEFAULT_CHARACTER = "教师"
    DEFAULT_CHARACTERISTIC = "精通编程且善于讲解的温柔大学女老师"
    AUDIO_LANGUAGE = "zh"


# ==================== 模型加载 ====================
@st.cache_resource
def load_whisper_model(model_name: str = Config.WHISPER_MODEL):
    """加载 Whisper 语音识别模型"""
    return whisper.load_model(model_name)


# ==================== 初始化配置 ====================
def init_page_config():
    """初始化页面配置"""
    st.set_page_config(
        page_title=Config.PAGE_TITLE,
        layout="wide",
        initial_sidebar_state="auto",
        page_icon=Config.PAGE_ICON,
    )


def init_openai_client() -> OpenAI:
    """初始化模型客户端"""
    return OpenAI(
        api_key=Config.DEEPSEEK_API_KEY,
        base_url=Config.DEEPSEEK_BASE_URL
    )


# ==================== 侧边栏 ====================
def render_sidebar() -> bool:
    """渲染侧边栏并返回伴侣信息和会话管理"""
    with st.sidebar:
        st.subheader("会话管理")
        session_management()

        st.subheader("角色信息")
        character_management()

        # 分割符
        st.divider()

        st.subheader("输出设置")
        use_stream = st.checkbox("启用流式输出", value=True,
                                 help="流式输出：逐字显示；非流式输出：一次性显示完整回复")

    return use_stream


def session_management():
    # 会话管理
    if not os.path.exists("Resources/Sessions"):
        os.makedirs("Resources/Sessions", exist_ok=True)
    for session in os.listdir("Resources/Sessions"):
        if session.endswith(".json") and st.button(session):
            st.session_state.session_id = session[:-5]
            load_current_state()#能刷新界面
            print("加载会话"+st.session_state.session_id)

    if st.button("创建新对话") and st.session_state.messages:
        # 保存当前会话
        save_current_session()
        print(st.session_state.session_id+"保存成功")
        # 初始化新会话并保存

        st.session_state.messages = []
        st.session_state.current_session = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.session_id = st.session_state.current_session
        print("初始化新会话完成")
        save_current_session()
        print(st.session_state.session_id+"保存成功")
        load_current_state()# 不能刷新界面？
        print(f"加载新对话{st.session_state.session_id}完成")


def character_management():
    # 角色管理
    st.session_state["nick_name"] = st.text_input("角色名称", Config.DEFAULT_NICKNAME)
    st.session_state["character"] = st.text_area("角色类型（伴侣，教师...）", Config.DEFAULT_CHARACTER)
    st.session_state.characteristic = st.text_area("角色性格特点", Config.DEFAULT_CHARACTERISTIC)
    return


# ==================== 提示词生成 ====================
def build_system_prompt(nick_name: str, character: str, characteristic: str) -> str:
    """构建系统提示词"""
    return f"""你叫{nick_name}，现在是一个{character}，请完全代入角色。
                规则:
                    1.如果用户想要学习知识请把你认为用户可能不懂的特殊名词解释一下
                    2.禁止任何场景或状态描述性文字
                    3.匹配用户的语言
                    4.请用下划线标出专业术语，并在回答末尾以‘术语解释：’为标题列出这些术语的简明定义
                    5.有需要的话可以用❤️🌸等 emoji 表情
                    6.用符合角色性格的方式对话
                    7.回复的内容，要充分体现角色的性格特征
                    8.如果用户不是很理解可以稍微详细的解释一下
                伴侣性格：- {characteristic}
                你必须严格遵守上述规则来回复用户。"""


# ==================== 聊天记录管理 ====================
def init_chat_history():
    """初始化聊天记录"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_session" not in st.session_state:
        st.session_state.current_session = datetime.now().strftime("%Y%m%d_%H%M%S")
    # if "nick_name" not in st.session_state:
    #     st.session_state.nick_name = Config.DEFAULT_NICKNAME
    # if "character" not in st.session_state:
    #     st.session_state.character = Config.DEFAULT_CHARACTER
    # if "characteristic" not in st.session_state:
    #     st.session_state.characteristic = Config.DEFAULT_CHARACTERISTIC
    # if "current_session" is not st.session_state.current_session:
    #     st.session_state.current_session = datetime.now().strftime("%Y%m%d_%H%M%S")
    #
    # if "messages" is not st.session_state.messages or "messages" not in st.session_state:
    #     st.session_state.messages = []
    #
    # if "nick_name" is not st.session_state.nick_name or "nick_name" not in st.session_state:
    #     st.session_state.nick_name = Config.DEFAULT_NICKNAME
    #
    # if "character" not in st.session_state.character or "character" not in st.session_state:
    #     st.session_state.character = Config.DEFAULT_CHARACTER
    #
    # if "characteristic" not in st.session_state.characteristic or "characteristic" not in st.session_state:
    #     st.session_state.characteristic = Config.DEFAULT_CHARACTERISTIC
    # if st.session_state.current_session is not datetime.now().strftime("%Y%m%d_%H%M%S"):
    #     st.session_state.current_session = datetime.now().strftime("%Y%m%d_%H%M%S")
    # if st.session_state.messages is not st.session_state.get("messages", []):
    #     st.session_state.messages = []
    # if st.session_state.nick_name is not st.session_state.get("nick_name", Config.DEFAULT_NICKNAME):
    #     st.session_state.nick_name = Config.DEFAULT_NICKNAME
    # if st.session_state.character is not st.session_state.get("character", Config.DEFAULT_CHARACTER):
    #     st.session_state.character = Config.DEFAULT_CHARACTER
    # if st.session_state.characteristic is not st.session_state.get("characteristic", Config.DEFAULT_CHARACTERISTIC):
    #     st.session_state.characteristic = Config.DEFAULT_CHARACTERISTIC

    # st.session_state.messages = st.session_state.get("messages", [])
    # st.session_state.nick_name = st.session_state.get("nick_name", Config.DEFAULT_NICKNAME)
    # st.session_state.character = st.session_state.get("character", Config.DEFAULT_CHARACTER)
    # st.session_state.characteristic = st.session_state.get("characteristic", Config.DEFAULT_CHARACTERISTIC)


def display_chat_history():
    """显示聊天记录"""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])


def add_to_chat_history(role: str, content: str):
    """添加消息到聊天记录"""
    st.session_state.messages.append({"role": role, "content": content})


# ===================== 文件管理 ====================
def save_current_session():
    """保存当前会话"""
    session_data = {"messages": st.session_state.messages,
                    "nick_name": st.session_state.nick_name,
                    "character": st.session_state.character,
                    "characteristic": st.session_state.characteristic,
                    "current_session": st.session_state.current_session
                    }
    if st.session_state.current_session:
        with open(f"Resources/Sessions/{st.session_state.current_session}.json", "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False)


def load_current_state():
    """加载当前会话"""
    print("开始加载会话"+st.session_state.session_id)
    if os.path.exists(f"Resources/Sessions/{st.session_state.session_id}.json"):
        with open(f"Resources/Sessions/{st.session_state.session_id}.json", "r", encoding="utf-8") as f:
            session_data: dict = json.load(f)
            st.session_state.messages = session_data.get("messages", [])
            st.session_state.nick_name = session_data.get("nick_name", Config.DEFAULT_NICKNAME)
            st.session_state.character = session_data.get("character", Config.DEFAULT_CHARACTER)
            st.session_state.characteristic = session_data.get("characteristic", Config.DEFAULT_CHARACTERISTIC)
            st.session_state.current_session = session_data.get("current_session", "")
    print("开始rerun")
    st.rerun()


# ==================== 语音处理 ====================
def process_audio(audio_bytes: bytes, model) -> str:
    """处理音频并返回转写文本"""
    if not audio_bytes:
        return ""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        result = model.transcribe(tmp_path, language=Config.AUDIO_LANGUAGE, fp16=False)
        return result["text"]
    finally:
        os.unlink(tmp_path)


# ==================== AI 对话 ====================
def get_ai_response(client: OpenAI, system_prompt: str, messages: list, stream: bool = True):
    """获取 AI 响应"""
    response = client.chat.completions.create(
        model=Config.DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            *messages
        ],
        stream=stream
    )
    return response


def display_streaming_response(response, message_container):
    """显示流式响应"""
    full_response = ""
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            full_response += content
            message_container.write(full_response)
            print(f"AI 输出：{full_response}")
    return full_response


def display_normal_response(response):
    """显示非流式响应"""
    full_response = response.choices[0].message.content
    print(f"AI 输出：{full_response}")
    return full_response


# ==================== 主函数 ====================
def main():
    """应用主函数"""
    # 初始化配置
    init_page_config()

    # 加载模型
    stt_model = load_whisper_model()

    # 初始化客户端
    client = init_openai_client()

    # 显示标题
    st.title(Config.PAGE_TITLE)

    # 渲染侧边栏
    use_stream = render_sidebar()

    # 构建提示词
    system_prompt = build_system_prompt(st.session_state.nick_name,
                                        st.session_state.character,
                                        st.session_state.characteristic)

    # 初始化聊天记录
    init_chat_history()

    # 显示历史消息
    display_chat_history()

    # 处理用户输入
    if prompt := st.chat_input(
            "Say or record something",
            accept_audio=True,
            accept_file=True
    ):
        user_text = None

        # 处理音频输入
        if prompt and prompt.audio:
            audio_bytes = prompt.audio.read()
            user_text = process_audio(audio_bytes, stt_model)
            print(f"用户语音输入：{user_text}")

        # 处理文本输入
        if prompt and prompt.text:
            user_text = prompt.text
            print(f"用户输入：{prompt}")

        # 显示并保存用户消息
        if user_text:
            st.chat_message("user").write(user_text)
            add_to_chat_history("user", user_text)

            # 获取 AI 响应
            response = get_ai_response(client, system_prompt, st.session_state.messages, stream=use_stream)

            # 根据设置选择显示方式
            with st.chat_message("assistant"):
                if use_stream:
                    # 流式输出
                    full_response = display_streaming_response(response, st.empty())
                else:
                    # 非流式输出
                    full_response = display_normal_response(response)
                    st.write(full_response)

            # terms = re.findall(r'_\w+_', full_response)
            # for term in terms:
            #     print(f"术语：{term}")

            # 保存 AI 响应
            add_to_chat_history("assistant", full_response)
            print(f"最终回复：{full_response}")

            # 保存当前会话
            save_current_session()


if __name__ == "__main__":
    main()
