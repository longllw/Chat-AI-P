import os
import tempfile
import streamlit as st
from dotenv import load_dotenv
from langchain.chains.conversation.base import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import ChatOpenAI
import shutil  # 新增导入


def get_ai_response_for_document_analysis(user_prompt, model_version, temperature, document_content):
    """专门用于文档分析的AI响应获取函数"""
    try:
        load_dotenv()
        # 使用有效的全局API密钥和标准端点
        model = ChatOpenAI(
            model=model_version,
            temperature=temperature,
            base_url='https://api.openai-hk.com/v1',
            api_key=st.secrets["API_KEY"]  # 从secrets获取密钥
            #api_key='hk-udshhb100005545665385f81a2983037bba4cf7952008c39',
        )

        # 构造包含文档内容的完整提示
        full_prompt = f"用户的问题是：{user_prompt}\n\n文档内容：{document_content}\n\n请根据文档内容回答用户的问题。"

        # 使用会话状态中的内存对象
        chain = ConversationChain(llm=model, memory=st.session_state.memory)
        return chain.invoke({'input': full_prompt})['response']
    except Exception as err:
        st.error(f"发生错误：{err}")
        return '暂时无法获取服务器响应……'


def document_analysis():
    """文档分析功能"""
    st.title("文档分析智能体")

    # 初始化会话状态 - 使用ConversationBufferMemory
    if 'memory' not in st.session_state:
        st.session_state.memory = ConversationBufferMemory()

    # 初始化文档内容
    if 'document_content' not in st.session_state:
        st.session_state.document_content = ""

    # 文档上传和读取
    uploaded_file = st.file_uploader("上传你的文档", type=["pdf", "txt"])
    if uploaded_file:
        try:
            file_type = uploaded_file.name.split('.')[-1].lower()
            # 创建一个更安全的临时目录
            temp_dir = tempfile.mkdtemp()
            temp_file_path = os.path.join(temp_dir, uploaded_file.name)
            # 将上传的文件写入临时位置
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            if file_type == "txt":
                # 直接读取文本文件内容
                with open(temp_file_path, "r", encoding="utf-8") as f:
                    st.session_state.document_content = f.read()
            elif file_type == "pdf":
                # 使用PyPDFLoader处理PDF文件
                loader = PyPDFLoader(file_path=temp_file_path)
                docs = loader.load_and_split()
                full_text = "\n".join([doc.page_content for doc in docs])
                st.session_state.document_content = full_text
            st.success("文档读取成功！")
        except Exception as e:
            st.error(f"读取文档时出错：{e}")
            st.exception(e)
        finally:
            # 清理临时目录
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    st.warning(f"清理临时文件时出错: {e}")
    # 显示文档内容
    if st.session_state.document_content:
        with st.expander("查看/折叠文档内容"):
            st.subheader("文档内容")
            st.write(st.session_state.document_content)

    # 侧边栏配置
    with st.sidebar:
        with st.expander("模型配置"):
            model_version = st.selectbox("选择模型版本", ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"])
            temperature = st.slider("设置模型温度", min_value=0.1, max_value=1.0, value=0.7, step=0.1)

        # 添加重置内存按钮
        if st.button("重置对话记忆"):
            st.session_state.memory = ConversationBufferMemory()
            st.success("对话记忆已重置!")

    # 用户输入区域
    user_query = st.text_input("请输入你的问题：")
    generate_response = st.button("生成回答")

    if generate_response and user_query and st.session_state.document_content:
        with st.spinner('AI正在思考，请等待……'):
            resp_from_ai = get_ai_response_for_document_analysis(
                user_query,
                model_version,
                temperature,
                st.session_state.document_content
            )
            st.subheader("AI的回答")
            st.write(resp_from_ai)