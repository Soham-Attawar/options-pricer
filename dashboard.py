# ============================================================
# NIFTY OPTIONS PRICER - Streamlit Dashboard v2
# ============================================================

# --- IMPORTS ---
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from core import price_option

import importlib
import market_data
importlib.reload(market_data)

get_nifty_price = market_data.get_nifty_price
get_nifty_volatility = market_data.get_nifty_volatility
get_next_expiry = market_data.get_next_expiry
get_monthly_expiry = market_data.get_monthly_expiry
get_banknifty_price = market_data.get_banknifty_price
get_banknifty_volatility = market_data.get_banknifty_volatility
get_banknifty_expiry = market_data.get_banknifty_expiry

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Nifty Options Pricer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LOAD CSS ---
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("styles.css")

# --- HEADER ---
st.markdown("""
    <div class="main-header">
        <h1>📈 Nifty Options Pricer</h1>
        <p>Professional options pricing using Monte Carlo simulation & Black-Scholes model</p>
    </div>
""", unsafe_allow_html=True)

# --- SIDEBAR PART 1 - Index Selection ---
with st.sidebar:
    st.markdown("## ⚙️ Configure Option")
    st.markdown("---")

    st.markdown("### 📌 Select Index")
    index_choice = st.radio(
        "Choose Index",
        ["Nifty 50", "BankNifty"],
        help="Nifty 50 expires Thursday, BankNifty expires Wednesday"
    )
    st.markdown("---")

# --- FETCH MARKET DATA ---
with st.spinner("Fetching live market data..."):
    if index_choice == "Nifty 50":
        S0 = get_nifty_price()
        sigma = get_nifty_volatility()
        weekly_date, weekly_T, weekly_days = get_next_expiry()
        monthly_date, monthly_T, monthly_days = get_monthly_expiry()
        index_name = "Nifty 50"
    else:
        S0 = get_banknifty_price()
        sigma = get_banknifty_volatility()
        weekly_date, weekly_T, weekly_days = get_banknifty_expiry()
        monthly_date, monthly_T, monthly_days = get_monthly_expiry()
        index_name = "BankNifty"

# --- SIDEBAR PART 2 - Rest of inputs ---
with st.sidebar:
    st.markdown(f"### 🏦 {index_name}")
    st.markdown(f"## ₹{S0:,.2f}")
    st.markdown(f"Volatility: **{sigma*100:.2f}%** | RBI Rate: **6.5%**")
    st.markdown("---")

    st.markdown("### 📅 Expiry")
    expiry_type = st.radio(
        "Select Expiry Type",
        ["Weekly", "Monthly"],
        help="Nifty: Weekly=Thursday | BankNifty: Weekly=Wednesday"
    )

    if expiry_type == "Weekly":
        expiry_date = weekly_date
        T = weekly_T
        days_remaining = weekly_days
        paths = 100000
    else:
        expiry_date = monthly_date
        T = monthly_T
        days_remaining = monthly_days
        paths = 50000

    st.info(f"📅 {expiry_date}\n\n⏳ {days_remaining} days away")

    st.markdown("### 🎯 Strike Price")
    suggested_strike = round(S0 / 100) * 100 + 500
    K = st.number_input(
        "Strike Price (₹)",
        min_value=10000,
        max_value=100000,
        value=int(suggested_strike),
        step=50,
        help="Enter the option strike price"
    )

    distance = K - S0
    distance_pct = (distance / S0) * 100
    if distance > 0:
        st.markdown(f"📊 Strike is **₹{distance:.0f} ({distance_pct:.1f}%) above** current price")
    else:
        st.markdown(f"📊 Strike is **₹{abs(distance):.0f} ({abs(distance_pct):.1f}%) below** current price")

    st.markdown("---")
    calculate = st.button("🚀 Calculate Option Price", type="primary", use_container_width=True)

# --- LIVE MARKET DATA ---
st.markdown("### 📊 Live Market Data")
col1, col2, col3, col4 = st.columns(4)
col1.metric(f"{index_name} Price", f"₹{S0:,.2f}")
col2.metric("Historical Volatility", f"{sigma*100:.2f}%")
col3.metric("Risk Free Rate (RBI)", "6.5%")
col4.metric("Days to Expiry", f"{days_remaining} days")

st.markdown("---")

# --- MAIN CONTENT ---
if calculate:

    with st.spinner("Running Monte Carlo simulation..."):
        results = price_option(S0, K, T, r=0.065, sigma=sigma, paths=paths)

    # --- OPTION PRICES ---
    st.markdown("### 💰 Option Prices")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📗 Call Option")
        st.metric("Monte Carlo Price", f"₹{results['call_price']:.2f}")
        st.metric("Black-Scholes Price", f"₹{results['BS_call']:.2f}")
        st.metric("Difference", f"₹{abs(results['BS_call'] - results['call_price']):.2f}")

    with col2:
        st.markdown("#### 📕 Put Option")
        st.metric("Monte Carlo Price", f"₹{results['put_price']:.2f}")
        st.metric("Black-Scholes Price", f"₹{results['BS_put']:.2f}")
        st.metric("Difference", f"₹{abs(results['BS_put'] - results['put_price']):.2f}")

    # --- GREEKS ---
    st.markdown("### 🔢 Greeks")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Delta (Call)", f"{results['delta_call']:.4f}")
    col2.metric("Delta (Put)", f"{results['delta_put']:.4f}")
    col3.metric("Gamma", f"{results['gamma']:.6f}")
    col4.metric("Theta (Call)/day", f"₹{results['theta_call']:.2f}")
    col5.metric("Vega (1% vol)", f"₹{results['vega']:.2f}")

    st.markdown("---")

    # --- TABS ---
    tab1, tab2, tab3 = st.tabs(["📈 Price Paths", "💹 Payoff Diagram", "⚠️ Risk Analysis"])

    with tab1:
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(results['paths'][:, :100], alpha=0.2, linewidth=0.5)
        ax.axhline(y=K, color='red', linestyle='--', linewidth=2, label=f'Strike ₹{K}')
        ax.axhline(y=S0, color='green', linestyle='--', linewidth=2, label=f'Current ₹{S0}')
        ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
        ax.set_title(f'Monte Carlo Simulation - {paths:,} paths')
        ax.set_xlabel('Trading Days')
        ax.set_ylabel(f'{index_name} Price (₹)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)

    with tab2:
        nifty_range = np.linspace(S0 * 0.7, S0 * 1.3, 500)
        call_payoff = np.maximum(nifty_range - K, 0) - results['call_price']
        put_payoff = np.maximum(K - nifty_range, 0) - results['put_price']

        fig2, ax2 = plt.subplots(figsize=(12, 5))
        ax2.plot(nifty_range, call_payoff, color='green', linewidth=2, label='Call Option P&L')
        ax2.plot(nifty_range, put_payoff, color='red', linewidth=2, label='Put Option P&L')
        ax2.axhline(y=0, color='white', linewidth=1, linestyle='-')
        ax2.axvline(x=K, color='yellow', linewidth=1.5, linestyle='--', label=f'Strike ₹{K}')
        ax2.axvline(x=S0, color='cyan', linewidth=1.5, linestyle='--', label=f'Current ₹{S0}')
        ax2.fill_between(nifty_range, call_payoff, 0,
                         where=(call_payoff > 0), color='green', alpha=0.1)
        ax2.fill_between(nifty_range, put_payoff, 0,
                         where=(put_payoff > 0), color='red', alpha=0.1)
        ax2.set_title('Option Payoff at Expiry')
        ax2.set_xlabel(f'{index_name} Price at Expiry (₹)')
        ax2.set_ylabel('Profit / Loss (₹)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        st.pyplot(fig2)

    with tab3:
        nifty_returns = (results['final_prices'] - S0) / S0
        var_95 = np.percentile(nifty_returns, 5)
        var_99 = np.percentile(nifty_returns, 1)
        cvar_95 = nifty_returns[nifty_returns <= var_95].mean()

        var_95_rs = abs(var_95 * S0)
        var_99_rs = abs(var_99 * S0)
        cvar_95_rs = abs(cvar_95 * S0)

        call_pnl = np.maximum(results['final_prices'] - K, 0) - results['call_price']
        put_pnl = np.maximum(K - results['final_prices'], 0) - results['put_price']

        st.markdown("#### 📉 Index Risk")
        col1, col2, col3 = st.columns(3)
        col1.metric(f"VaR 95% ({index_name})", f"₹{var_95_rs:.2f}", f"{var_95*100:.2f}%")
        col2.metric(f"VaR 99% ({index_name})", f"₹{var_99_rs:.2f}", f"{var_99*100:.2f}%")
        col3.metric(f"CVaR 95% ({index_name})", f"₹{cvar_95_rs:.2f}", f"{cvar_95*100:.2f}%")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📗 Call Option Risk")
            st.metric("Max Loss (Premium Paid)", f"₹{results['call_price']:.2f}")
            st.metric("Max Profit Potential", f"₹{call_pnl.max():.2f}")
            profitable = (call_pnl > 0).sum() / len(call_pnl) * 100
            st.metric("Probability of Profit", f"{profitable:.1f}%")

        with col2:
            st.markdown("#### 📕 Put Option Risk")
            st.metric("Max Loss (Premium Paid)", f"₹{results['put_price']:.2f}")
            st.metric("Max Profit Potential", f"₹{put_pnl.max():.2f}")
            profitable_put = (put_pnl > 0).sum() / len(put_pnl) * 100
            st.metric("Probability of Profit", f"{profitable_put:.1f}%")

        fig3, ax3 = plt.subplots(figsize=(12, 4))
        ax3.hist(nifty_returns * 100, bins=100, color='blue', alpha=0.6, edgecolor='none')
        ax3.axvline(x=var_95*100, color='orange', linewidth=2,
                    linestyle='--', label=f'VaR 95%: {var_95*100:.2f}%')
        ax3.axvline(x=var_99*100, color='red', linewidth=2,
                    linestyle='--', label=f'VaR 99%: {var_99*100:.2f}%')
        ax3.axvline(x=0, color='white', linewidth=1)
        ax3.set_title(f'{index_name} Return Distribution at Expiry')
        ax3.set_xlabel('Return (%)')
        ax3.set_ylabel('Frequency')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        st.pyplot(fig3)

else:
    st.markdown("### 👈 Configure your option in the sidebar and click Calculate")
    st.markdown("""
        **How to use:**
        1. Select Nifty 50 or BankNifty in the sidebar
        2. Select Weekly or Monthly expiry
        3. Enter your desired strike price
        4. Click Calculate Option Price
        5. View pricing, Greeks, payoff diagram and risk analysis
    """)