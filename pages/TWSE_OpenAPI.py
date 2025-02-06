import streamlit as st
from twse_openapi import TwseOpenApi
import plotly.express as px

st.set_page_config(page_title="TWSE OpenAPI", layout="centered")
st.title("TWSE OpenAPI")

twse_api = TwseOpenApi()


st.header("Industry EPS Statistics Data")

st.link_button(
    "Industry EPS Statistics Data",
    "https://openapi.twse.com.tw/#/%E5%85%AC%E5%8F%B8%E6%B2%BB%E7%90%86/get_opendata_t187ap14_L",
)
df_industry_eps = twse_api.get_industry_eps_stat_info()
st.dataframe(df_industry_eps)

# # Plot with Plotly treemap
# # https://plotly.com/python/treemaps/
# # https://plotly.com/python-api-reference/generated/plotly.express.treemap
fig = px.treemap(
    df_industry_eps,
    path=["產業別", "公司名稱"],
    # path=["公司名稱"],
    values="基本每股盈餘(元)",
    title="Industry EPS",
    # color="change_pct",
    # color_continuous_scale=["red", "white", "green"],
    # range_color=[-20, 20],
    # hover_data={"custom_text": True},  # Display custom text on hover
)
#
# # Update layout and text display
# fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
# # https://plotly.com/python/reference/treemap/#treemap-textinfo
# fig.update_traces(textinfo="label+value+percent parent")
# fig.update_traces(textinfo="text+label")
#
st.plotly_chart(fig)
