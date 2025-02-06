import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.title("TWSE Trading Cost")

"""
- [股票手續費計算方式是什麼？各大券商股票交易手續費/折扣總整理 - Mr.Market市場先生](https://rich01.com/stock-commission-fee/)
- [集中市場交易制度介紹 - TWSE 臺灣證券交易所](https://www.twse.com.tw/zh/products/system/trading.html)
- [買股票手續費如何計算？先瞭解證券交易成本，才能節省投資支出](https://www.masterlink.com.tw/transaction-costs)
- [股票升降單位](https://concords.moneydj.com/z/glossary/glexp_4792.djhtm)
"""

with st.expander("Figures"):
    """
    ![買賣股票的交易成本](https://rich01.com/wp-content/uploads/2024/07/20250113143636_0_f9587d.jpg)
    ![股票手續費與交易稅計算方式](https://rich01.com/wp-content/uploads/2024/07/20250113133655_0_cb733a.jpg)
    """

original_commission = st.number_input(
    "Commission (手續費)",
    value=0.001425,
    format="%.6f",  # display with 4 decimal places
    help="買賣股票皆需承擔手續費。",
)
tax = st.number_input(
    "Tax (交易稅)",
    value=0.0015,
    format="%.4f",  # display with 4 decimal places
    step=0.0001,
    help="賣出股票要承擔交易稅，現股 0.3%、當沖 0.15%、ETF 0.1%。",
)
commission_discount = st.number_input(
    "Commission Discount (手續費折扣)",
    value=0.6,
    min_value=0.0,
    max_value=1.0,
    step=0.1,
    help="手續費折扣，不同券商會提供不同折扣，一般行情價為5~6折。",
)

commission = original_commission * commission_discount

trading_cost = original_commission * commission_discount * 2 + tax

f"""
$$
p \\times (({original_commission * 100:.4f}\\% \\times {commission_discount}) \\times 2 + {tax * 100:.2f}\\%) = p \\times {trading_cost * 100:.4f}\\%
$$
"""

st.caption(f"(i.e. Trading Cost equals {trading_cost * 10000} bps)")


# --------------- 1. 基本參數設定 ---------------
min_price = 1  # 模擬的最小股價
max_price = 2000  # 模擬的最大股價
num_points = 2000  # 在區間內取多少個點

prices = np.linspace(min_price, max_price, num_points)


# --------------- 2. 定義跳價規則 ---------------
def tick_size(price: float) -> float:
    """
    根據台股現股規則，傳回股價 p 的"每檔跳價" (單位: TWD)
    """
    if price < 10:
        return 0.01
    elif price < 50:
        return 0.05
    elif price < 100:
        return 0.1
    elif price < 500:
        return 0.5
    elif price < 1000:
        return 1
    else:
        return 5


# --------------- 3. 定義「買1張 + 賣1張」交易總成本 ---------------
def total_transaction_cost_twd(
    price: float, commission: float, tax: float, shares: float = 1000
) -> float:
    """
    回傳買進1張 + 賣出1張股票(各1,000股)時，所有費用的總和 (TWD)。
    包含：
    - 買進手續費（至少 20 元）
    - 賣出手續費（至少 20 元）
    - 賣出交易稅 0.3%
    """
    # 買進手續費
    buy_fee = price * shares * commission
    if buy_fee < 20:
        buy_fee = 20

    # 賣出手續費
    sell_fee = price * shares * commission
    if sell_fee < 20:
        sell_fee = 20

    # 證券交易稅 (只賣出收)
    tax = price * shares * tax

    # 總和
    return buy_fee + sell_fee + tax


# --------------- 4. 計算各股價下的「跳價成本 (bps)」與「總交易成本 (bps)」 ---------------
tick_bps = []
trans_bps = []

for p in prices:
    # (a) 跳價成本 (對1股來說是 tick_size(p) TWD，但我們轉成"相對於股價的bps")
    #     這裡先針對「股價1股」的 bp。
    #     如果要對「一張」的價值做對比，可同理將 tick_size(p)*1000 與 p*1000 相比，
    #     但結果在 bps 上其實相同，所以我們仍以 1 股為單位計算即可。
    one_tick_bps = (tick_size(p) / p) * 10000
    tick_bps.append(one_tick_bps)

    # (b) 交易總成本 (買 + 賣) => 以 1 張(1000股) 總成本換算成對股價(1股)的 bps
    cost_twd = total_transaction_cost_twd(
        p,
        commission=commission,
        tax=tax,
    )
    # 1張的整體交易金額 = p * 1000；轉成與"1股股價"相對的bps => 除以 (p * 1000) 再乘以 10,000
    cost_bps = (cost_twd / (p * 1000)) * 10000
    trans_bps.append(cost_bps)

# --------------- 5. 畫圖：繪製兩條曲線並加上級距的垂直線 ---------------
fig = go.Figure()

# (A) 加入「每檔跳價成本 (bps)」曲線
fig.add_trace(go.Scatter(x=prices, y=tick_bps, mode="lines", name="每檔跳價 (bps)"))

# (B) 加入「總交易成本 (bps)」曲線
fig.add_trace(
    go.Scatter(x=prices, y=trans_bps, mode="lines", name="買+賣 總成本 (bps)")
)

# 垂直虛線(各級距分隔)
vertical_lines = [10, 50, 100, 500, 1000]
for v in vertical_lines:
    fig.add_shape(
        dict(
            type="line",
            x0=v,
            x1=v,
            y0=0,
            y1=max(max(tick_bps), max(trans_bps)),
            line=dict(color="red", dash="dot"),
            xref="x",
            yref="y",
        )
    )

# 設定圖表
fig.update_layout(
    title="台股「每檔跳價」vs「總交易成本」(bps) 曲線",
    xaxis_title="股價 (TWD)",
    yaxis_title="成本 (bps)",
    showlegend=True,
)

st.plotly_chart(fig)


# ============= 4. 計算「每檔跳價(1張)」 vs. 「總交易成本(1張)」 =============
tick_values = []  # 1 檔跳價（1張）的 TWD
trans_costs = []  # 買+賣 (1張) 的 TWD

for p in prices:
    # 1檔跳價(1張) = 跳價(單股) × 1000
    tick_val = tick_size(p) * 1000
    tick_values.append(tick_val)

    # 買+賣一次交易的總成本 (TWD)
    cost = total_transaction_cost_twd(p, commission=commission, tax=tax)
    trans_costs.append(cost)

# ============= 5. 繪圖 =============
fig = go.Figure()

# (A) 每檔跳價(1張) 曲線 (TWD)
fig.add_trace(
    go.Scatter(x=prices, y=tick_values, mode="lines", name="每檔跳價 (1張, TWD)")
)

# (B) 買+賣 總交易成本(1張) 曲線 (TWD)
fig.add_trace(
    go.Scatter(
        x=prices, y=trans_costs, mode="lines", name="買+賣 總交易成本 (1張, TWD)"
    )
)

# 6. 垂直虛線(各級距分隔)
vertical_lines = [10, 50, 100, 500, 1000]
for v in vertical_lines:
    fig.add_shape(
        type="line",
        x0=v,
        x1=v,
        y0=0,
        y1=max(max(tick_values), max(trans_costs)),
        line=dict(color="red", dash="dot"),
        xref="x",
        yref="y",
    )

# 7. 佈局設定
fig.update_layout(
    title="以「1張」為單位：每檔跳價 vs. 完整交易成本 (TWD)",
    xaxis_title="股價 (單股, TWD)",
    yaxis_title="金額 (TWD)",
    showlegend=True,
)

st.plotly_chart(fig)
