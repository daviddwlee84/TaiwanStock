import streamlit as st
from twse_openapi import TwseOpenApi

twse_api = TwseOpenApi()


st.link_button(
    "Industry EPS Statistics Data",
    "https://openapi.twse.com.tw/#/%E5%85%AC%E5%8F%B8%E6%B2%BB%E7%90%86/get_opendata_t187ap14_L",
)
df_industry_eps = twse_api.get_industry_eps_stat_info()
st.dataframe(df_industry_eps)
