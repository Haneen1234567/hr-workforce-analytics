import streamlit as st
import pandas as pd

st.set_page_config(page_title="HR Workforce Analytics", layout="wide")

st.title("HR Workforce Analytics Dashboard")

uploaded_file = st.file_uploader(
    "Upload Excel File",
    type=["xlsx"]
)

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.subheader("Data Preview")
    st.dataframe(df)

    st.success("File uploaded successfully")
