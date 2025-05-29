import openpyxl
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import plotly.express as px
from utils import dataframe_agent

def create_chart(input_data, chart_type):
    """生成统计图表"""
    df_data = pd.DataFrame(
        data={
            "x": input_data["columns"],
            "y": input_data["data"]
        }
    )

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


def create_data_analysis():
    """数据分析功能模块"""
    st.title("📊 数据分析智能体")
    st.caption("上传您的数据文件，获取智能分析结果")

    with st.container():
        col1, col2 = st.columns([1, 3])
        with col1:
            option = st.radio("数据文件类型:", ("Excel", "CSV"), horizontal=True)
        with col2:
            file_type = "xlsx" if option == "Excel" else "csv"
            data = st.file_uploader(f"上传{option}文件", type=file_type, label_visibility="collapsed")

    if data:
        if file_type == "xlsx":
            # 获取Excel文件的所有sheet名称
            excel_file = pd.ExcelFile(data)
            sheet_names = excel_file.sheet_names
            # 让用户选择要加载的sheet
            selected_sheet = st.selectbox("选择要加载的工作表:", sheet_names)
            # 加载选定的sheet
            st.session_state["df"] = pd.read_excel(data, sheet_name=selected_sheet)
        else:
            st.session_state["df"] = pd.read_csv(data)
        with st.expander("📋 原始数据预览", expanded=False):
            st.dataframe(st.session_state["df"], use_container_width=True)

    query = st.text_area(
        "💡 请输入您的分析需求:",
        placeholder="例如: 请分析销售额趋势\n或: 绘制各部门人数柱状图\n或: 绘制产品销量折线图",
        disabled="df" not in st.session_state,
        height=100
    )

    # 检查是否已上传文件
    if "df" not in st.session_state:
        st.info("请先上传数据文件")
        return

    button = st.button("🚀 开始分析", type="primary")

    if button:
        if not query.strip():
            st.warning("请输入分析需求")
        else:
            with st.spinner("AI正在思考中，请稍等..."):
                result = dataframe_agent(st.session_state["df"], query)
                if "answer" in result:
                    st.write(result["answer"])
                if "table" in result:
                    st.table(pd.DataFrame(result["table"]["data"],columns=result["table"]["columns"]))
                if "bar" in result:
                    create_chart(result["bar"], "bar")
                if "line" in result:
                    create_chart(result["line"], "line")
                if "pie" in result:
                    create_chart(result["pie"], "pie")
                if "scatter" in result:
                    create_chart(result["scatter"], "scatter")
                if "box" in result:
                    create_chart(result["box"], "box")
                if "hist" in result:
                    create_chart(result["hist"], "hist")
                if "area" in result:
                    create_chart(result["area"], "area")