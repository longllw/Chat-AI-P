import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from langchain.memory import ConversationBufferMemory
from langchain.chains.conversation.base import ConversationChain
from langchain_openai import ChatOpenAI
import warnings

from Data_Analysis import create_data_analysis
from document_analysis import document_analysis
import plotly.express as px
import pyperclip  # 用于复制文本

warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'].insert(0, 'SimHei')
plt.rcParams['axes.unicode_minus'] = False

# 设置全局样式
st.set_page_config(
    page_title="智能数据分析平台",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)


def set_custom_style():
    """设置自定义样式"""
    st.markdown("""
    <style>
        .main {padding: 2rem 1rem 4rem;}
        .stButton>button {width: 100%; border-radius: 8px;}
        .stTextArea textarea {border-radius: 8px;}
        .stRadio div[role="radiogroup"] {gap: 1rem;}
        .stRadio [data-baseweb="radio"] {margin-right: 5px;}
        .stFileUploader {border-radius: 8px; padding: 0.5rem;}
        .stChatMessage {padding: 1rem; border-radius: 12px;}
        .sidebar .sidebar-content {padding: 1rem;}
        [data-testid="stExpander"] {border-radius: 8px !important;}
        [data-testid="stExpander"] .streamlit-expanderHeader {font-weight: 600;}
        .feedback-container {display: flex; gap: 0.5rem; margin-top: 0.5rem;}
        .feedback-btn {padding: 0.25rem 0.5rem; font-size: 0.8rem;}
    </style>
    """, unsafe_allow_html=True)


set_custom_style()


def create_chart(input_data, chart_type):
    """生成统计图表"""
    if "columns" not in input_data:
        st.error("输入数据缺少 'columns' 键，请检查数据结构")
        return

    df_data = pd.DataFrame(
        data={
            "x": input_data["columns"],
            "y": input_data["data"]
        }
    )
    # ... 其余
    if chart_type == "bar":
        st.subheader("柱状图展示")
        fig = px.bar(df_data, x="x", y="y", title="柱状图")
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "line":
        st.subheader("折线图展示")
        fig = px.line(df_data, x="x", y="y", title="折线图", markers=True)
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "pie":
        st.subheader("饼图展示")
        fig = px.pie(df_data, names="x", values="y", title="饼图")
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "scatter":
        st.subheader("散点图展示")
        fig = px.scatter(df_data, x="x", y="y", title="散点图")
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "box":
        st.subheader("箱线图展示")
        fig = px.box(df_data, y="y", title="箱线图")
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "hist":
        st.subheader("直方图展示")
        fig = px.histogram(df_data, x="y", title="直方图")
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "area":
        st.subheader("面积图展示")
        fig = px.area(df_data, x="x", y="y", title="面积图")
        st.plotly_chart(fig, use_container_width=True)

def chat_module():
    """AI问答功能模块"""
    # 模型配置面板
    with st.sidebar.expander("⚙️ AI配置"):
        model_name = st.selectbox(
            "选择模型",
            ["gpt-3.5-turbo", "gpt-4", "gpt-4o-mini"],
            index=0
        )
        temperature = st.slider(
            "回答随机性",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.1,
            help="值越高回答越随机有创意"
        )
        presence_penalty = st.slider(
            "话题新鲜度",
            min_value=-2.0,
            max_value=2.0,
            value=0.0,
            step=0.1,
            help="正值避免重复话题，负值鼓励话题延续"
        )

    def get_ai_response(user_prompt):
        try:
            model = ChatOpenAI(

                base_url='https://twapi.openai-hk.com/v1',
                #api_key='hk-udshhb100005545665385f81a2983037bba4cf7952008c39',
                api_key=st.secrets['API_KEY'],
                model=model_name,
                temperature=temperature,
                presence_penalty=presence_penalty,
            )
            if 'memory' not in st.session_state:
                st.session_state['memory'] = ConversationBufferMemory(return_messages=True)
            chain = ConversationChain(llm=model, memory=st.session_state['memory'])
            return chain.run(input=user_prompt)
        except Exception as err:
            print(f"Error: {err}")
            return '暂时无法获取服务器响应……'

    st.title('💬 AI智能助手')
    st.caption("与AI进行自然对话，获取专业建议")

    # 初始化session状态
    if 'messages' not in st.session_state:
        st.session_state['messages'] = [
            {'role': 'ai', 'content': '您好！我是您的AI助手，很高兴为您服务。有什么我可以帮助您的吗？'}]
    if 'feedback' not in st.session_state:
        st.session_state['feedback'] = {}
    if 'regenerate' not in st.session_state:
        st.session_state['regenerate'] = {}

    def handle_feedback(message_id, is_like):
        """处理用户反馈"""
        st.session_state['feedback'][message_id] = 'like' if is_like else 'dislike'
        st.toast("感谢您的反馈！" if is_like else "我们会改进回答质量！")

    def handle_regenerate(message_id, prompt):
        """重新生成回答"""
        st.session_state['regenerate'][message_id] = True
        with st.spinner('重新生成回答中...'):
            response = get_ai_response(prompt)
            # 更新消息内容
            for msg in st.session_state['messages']:
                if msg.get('id') == message_id:
                    msg['content'] = response
                    msg['regenerated'] = True
                    break

    def copy_to_clipboard(text):
        """复制文本到剪贴板"""
        pyperclip.copy(text)
        st.toast("已复制到剪贴板！")

    # 聊天历史显示
    chat_container = st.container()
    with chat_container:
        for i, message in enumerate(st.session_state['messages']):
            role, content = message['role'], message['content']
            with st.chat_message(role):
                st.write(content)

                # 为AI回复添加操作按钮
                if role == 'ai':
                    # 为每条消息生成唯一ID
                    message_id = f"msg_{i}"
                    if 'id' not in message:
                        message['id'] = message_id

                    # 操作按钮容器 - 放在消息内容下方
                    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 4])

                    with col1:
                        st.button("📋", key=f"copy_{message_id}",
                                  help="复制回答内容",
                                  on_click=copy_to_clipboard,
                                  args=(content,))

                    with col2:
                        st.button("🔄", key=f"regenerate_{message_id}",
                                  help="让AI重新生成回答",
                                  on_click=handle_regenerate,
                                  args=(message_id, st.session_state['messages'][i - 1]['content'] if i > 0 else ""))

                    with col3:
                        st.button("👍", key=f"like_{message_id}",
                                  help="喜欢这个回答",
                                  on_click=handle_feedback,
                                  args=(message_id, True))

                    with col4:
                        st.button("👎", key=f"dislike_{message_id}",
                                  help="不喜欢这个回答",
                                  on_click=handle_feedback,
                                  args=(message_id, False))

                    with col5:
                        # 显示反馈状态
                        if message_id in st.session_state['feedback']:
                            feedback = st.session_state['feedback'][message_id]
                            st.write(f"您已标记为{'👍' if feedback == 'like' else '👎'}")
                        elif 'regenerated' in message and message['regenerated']:
                            st.write("🔄 已重新生成")

    # 用户输入
    if prompt := st.chat_input("请输入您的问题..."):
        with chat_container:
            # 添加用户消息
            user_msg = {'role': 'human', 'content': prompt}
            st.session_state['messages'].append(user_msg)
            st.chat_message("human").write(prompt)

            with st.spinner('AI正在思考...'):
                response = get_ai_response(prompt)
                # 添加AI回复
                ai_msg = {'role': 'ai', 'content': response}
                st.session_state['messages'].append(ai_msg)
                st.chat_message("ai").write(response)

def main():
    """主界面"""
    st.sidebar.header("功能导航")
    app_mode = st.sidebar.radio(
        "选择功能模式",
        ["💬 AI智能问答","📊 数据分析智能体","文档分析智能体"],
        index=0
    )

    st.sidebar.divider()
    st.sidebar.caption("v0.4 | 智能数据分析平台")

    if app_mode == "📊 数据分析智能体":
        create_data_analysis()
    elif app_mode=="文档分析智能体":
        document_analysis()
    else:
        chat_module()



if __name__ == "__main__":
    main()