# ============================================================
# NIFTY OPTIONS PRICER - Streamlit Dashboard v2
# ============================================================

# --- IMPORTS ---
import sys
import os
import math
import pandas as pd
from datetime import datetime
from scipy.stats import norm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import importlib
import core as core_module
importlib.reload(core_module)
price_option = core_module.price_option
price_option_with_separate_iv = core_module.price_option_with_separate_iv
calculate_implied_volatility = core_module.calculate_implied_volatility
adjust_iv_for_skew = core_module.adjust_iv_for_skew

import market_data
importlib.reload(market_data)

get_nifty_price = market_data.get_nifty_price
get_nifty_volatility = market_data.get_nifty_volatility
get_next_expiry = market_data.get_next_expiry
get_monthly_expiry = market_data.get_monthly_expiry
get_banknifty_price = market_data.get_banknifty_price
get_banknifty_volatility = market_data.get_banknifty_volatility
get_banknifty_expiry = market_data.get_banknifty_expiry
get_india_vix = market_data.get_india_vix
get_nse_option_price = market_data.get_nse_option_price
convert_date_to_nse_format = market_data.convert_date_to_nse_format
get_option_price_from_supabase = market_data.get_option_price_from_supabase
get_market_status = market_data.get_market_status
get_rbi_rate = market_data.get_rbi_rate
get_finnifty_price = market_data.get_finnifty_price
get_finnifty_volatility = market_data.get_finnifty_volatility
get_finnifty_expiry = market_data.get_finnifty_expiry
get_midcap_price = market_data.get_midcap_price
get_midcap_volatility = market_data.get_midcap_volatility
get_midcap_expiry = market_data.get_midcap_expiry
get_all_options_from_supabase = market_data.get_all_options_from_supabase
get_expiry_dates_from_supabase = market_data.get_expiry_dates_from_supabase

import portfolio as portfolio_module
importlib.reload(portfolio_module)
simulate_portfolio_pnl = portfolio_module.simulate_portfolio_pnl

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Nifty Options Pricer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- LOAD CSS ---
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("styles.css")

# --- MOBILE FIX CSS ---
st.markdown("""
    <style>
    @media (max-width: 768px) {
        .css-1d391kg { display: none; }
        .css-1lcbmhc { display: none; }
        [data-testid="collapsedControl"] { display: block; }
    }
    @media (max-width: 768px) {
        [data-testid="metric-container"] { width: 100% !important; }
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("""
    <div class="main-header">
        <h1>📈 Nifty Options Pricer</h1>
        <p>Risk management tools for Indian options traders</p>
    </div>
""", unsafe_allow_html=True)

# --- MARKET STATUS ---
market_status = get_market_status()
if market_status['is_open']:
    st.success(f"{market_status['status']} — {market_status['message']} | Prices update every 5 minutes")
elif market_status['color'] == 'yellow':
    st.warning(f"{market_status['status']} — {market_status['message']}")
else:
    st.info(f"{market_status['status']} — {market_status['message']} | Showing last closing prices")

# --- NAVIGATION ---
page = st.radio(
    "Navigation",
    ["🏠 Option Pricer", "📊 Portfolio VaR", "🔍 IV Analysis"],
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("---")

# ============================================================
# PAGE 1 - OPTION PRICER
# ============================================================
if page == "🏠 Option Pricer":

    with st.sidebar:
        st.markdown("## ⚙️ Configure")
        st.markdown("---")

        st.markdown("### 📌 Index")
        index_choice = st.selectbox(
            "Choose Index",
            ["Nifty 50", "BankNifty", "FinNifty", "MidcapNifty"],
            label_visibility="collapsed",
            help="Nifty 50 = top 50 companies | BankNifty = banking stocks | FinNifty = financial services | MidcapNifty = midcap select"
        )
        st.markdown("---")

    with st.spinner("Fetching live data..."):
        india_vix = get_india_vix()
        rbi_rate = get_rbi_rate()

        if index_choice == "Nifty 50":
            S0 = get_nifty_price()
            sigma_historical = get_nifty_volatility()
            sigma = india_vix if india_vix else sigma_historical
            weekly_date, weekly_T, weekly_days = get_next_expiry()
            monthly_date, monthly_T, monthly_days = get_monthly_expiry()
            index_name = "Nifty 50"
            nse_symbol = "NIFTY"
            lot_size = 65
        elif index_choice == "BankNifty":
            S0 = get_banknifty_price()
            sigma_historical = get_banknifty_volatility()
            sigma = india_vix if india_vix else sigma_historical
            weekly_date, weekly_T, weekly_days = get_banknifty_expiry()
            monthly_date, monthly_T, monthly_days = get_monthly_expiry()
            index_name = "BankNifty"
            nse_symbol = "BANKNIFTY"
            lot_size = 30
        elif index_choice == "FinNifty":
            S0 = get_finnifty_price()
            sigma_historical = get_finnifty_volatility()
            sigma = india_vix if india_vix else sigma_historical
            weekly_date, weekly_T, weekly_days = get_finnifty_expiry()
            monthly_date, monthly_T, monthly_days = get_monthly_expiry()
            index_name = "FinNifty"
            nse_symbol = "FINNIFTY"
            lot_size = 60
        else:
            S0 = get_midcap_price()
            sigma_historical = get_midcap_volatility()
            sigma = india_vix if india_vix else sigma_historical
            weekly_date, weekly_T, weekly_days = get_midcap_expiry()
            monthly_date, monthly_T, monthly_days = get_monthly_expiry()
            index_name = "MidcapNifty"
            nse_symbol = "MIDCPNIFTY"
            lot_size = 120

    with st.sidebar:
        if S0:
            st.markdown(f"### 🏦 {index_name}")
            st.markdown(f"## ₹{S0:,.2f}")
            rate_display = f"{rbi_rate*100:.2f}%" if rbi_rate else "N/A"
            if india_vix:
                st.markdown(f"VIX: **{india_vix*100:.2f}%** | Rate: **{rate_display}**")
            else:
                st.markdown(f"Vol: **{sigma*100:.2f}%** | Rate: **{rate_display}**")
        else:
            st.error(f"❌ {index_name} data unavailable")
        st.markdown("---")

        st.markdown("### 📅 Expiry")
        if index_choice == "Nifty 50":
            expiry_options = ["Weekly", "Monthly"]
        else:
            expiry_options = ["Monthly"]

        expiry_type = st.radio(
            "Expiry",
            expiry_options,
            label_visibility="collapsed",
            help="Weekly = expires this Tuesday | Monthly = expires last Tuesday of month"
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

        st.info(f"📅 {expiry_date} — {days_remaining} days away")

        st.markdown("### 🎯 Strike Price")
        if S0:
            suggested_strike = round(S0 / 100) * 100 + 500

            if index_choice == "Nifty 50":
                strike_min = 15000
                strike_max = 40000
                strike_step = 50
            elif index_choice == "BankNifty":
                strike_min = 40000
                strike_max = 80000
                strike_step = 100
            elif index_choice == "FinNifty":
                strike_min = 15000
                strike_max = 40000
                strike_step = 50
            else:
                strike_min = 8000
                strike_max = 25000
                strike_step = 25

            K = st.number_input(
                "Strike (₹)",
                min_value=strike_min,
                max_value=strike_max,
                value=int(suggested_strike),
                step=strike_step,
                label_visibility="collapsed",
                help="The fixed price at which you have the right to buy (call) or sell (put) the index at expiry"
            )

            distance = K - S0
            distance_pct = (distance / S0) * 100
            if distance > 0:
                st.caption(f"₹{distance:.0f} ({distance_pct:.1f}%) above current price")
            else:
                st.caption(f"₹{abs(distance):.0f} ({abs(distance_pct):.1f}%) below current price")
        else:
            K = 0
            st.error("Price data unavailable")

        st.markdown("---")

        st.markdown("### 💰 Position Sizing")
        account_size = st.number_input(
            "Account Size (₹)",
            min_value=10000,
            max_value=10000000,
            value=500000,
            step=10000,
            help="Your total trading capital"
        )
        risk_percent = st.slider(
            "Risk per trade (%)",
            min_value=0.5,
            max_value=5.0,
            value=2.0,
            step=0.5,
            help="Maximum % of your account you are willing to lose on this single trade. Professional traders use 1-2%."
        )

        st.markdown("---")
        calculate = st.button("🚀 Calculate", type="primary", use_container_width=True)

    # --- LIVE MARKET DATA ---
    st.markdown("### 📊 Live Market Data")
    col1, col2, col3, col4 = st.columns(4)
    if S0:
        col1.metric(f"{index_name}", f"₹{S0:,.2f}")
    else:
        col1.metric(f"{index_name}", "Unavailable")
    if india_vix:
        col2.metric(
            "India VIX",
            f"{india_vix*100:.2f}%",
            help="NSE's official fear index — higher VIX means options are more expensive. Above 20% = high fear."
        )
    else:
        col2.metric("Volatility", f"{sigma*100:.2f}%" if sigma else "Unavailable")
    col3.metric(
        "RBI Rate",
        f"{rbi_rate*100:.2f}%" if rbi_rate else "N/A",
        help="Current RBI repo rate — used as risk-free rate in option pricing formula"
    )
    col4.metric(
        "Days to Expiry",
        f"{days_remaining} days",
        help="Trading days remaining until option expires"
    )

    st.markdown("---")

    if calculate and S0 and K > 0:

        nse_expiry = convert_date_to_nse_format(expiry_date)

        with st.spinner("Fetching NSE prices..."):
            nse_call = get_nse_option_price(nse_symbol, K, nse_expiry, "CE")
            nse_put = get_nse_option_price(nse_symbol, K, nse_expiry, "PE")

        with st.spinner("Calculating..."):
            if not rbi_rate:
                st.error("❌ Unable to fetch RBI rate. Please try again.")
                st.stop()

            r = rbi_rate
            iv_call = None
            iv_put = None
            data_source = "historical"

            if nse_call and nse_call['lastPrice'] > 0:
                # Use NSE's own IV directly — eliminates circularity
                if nse_call.get('nseIV') and nse_call['nseIV'] > 0:
                    iv_call = nse_call['nseIV']
                else:
                    # Fallback — use midpoint price for IV calculation
                    price_for_iv = nse_call.get('midPrice', nse_call['lastPrice'])
                    iv_call = calculate_implied_volatility(
                        price_for_iv, S0, K, T, r, option_type='call'
                    )
                data_source = "live"

            if nse_put and nse_put['lastPrice'] > 0:
                # Use NSE's own IV directly — eliminates circularity
                if nse_put.get('nseIV') and nse_put['nseIV'] > 0:
                    iv_put = nse_put['nseIV']
                else:
                    # Fallback — use midpoint price for IV calculation
                    price_for_iv = nse_put.get('midPrice', nse_put['lastPrice'])
                    iv_put = calculate_implied_volatility(
                        price_for_iv, S0, K, T, r, option_type='put'
                    )
                data_source = "live"

            if iv_call:
                sigma_to_use = iv_call
            elif iv_put:
                sigma_to_use = iv_put
            elif india_vix:
                sigma_to_use = adjust_iv_for_skew(india_vix, S0, K, T)
                data_source = "vix"
            else:
                sigma_to_use = sigma
                data_source = "historical"

            if data_source == "live" and iv_call and iv_put:
                results = price_option_with_separate_iv(
                    S0, K, T, r, iv_call, iv_put, paths
                )
            else:
                results = price_option(S0, K, T, r=r, sigma=sigma_to_use, paths=paths)

        # Data source indicator
        if data_source == "live":
            nse_source = nse_call.get('source', 'live') if nse_call else 'unknown'
            if nse_source == 'supabase':
                updated = nse_call.get('updated_at', '')[:16] if nse_call else ''
                st.caption(f"📡 Data last updated: {updated}")
            else:
                st.caption(f"📡 Live NSE data")
        elif data_source == "vix":
            st.caption(f"📡 Using India VIX ({india_vix*100:.2f}%) — live option data unavailable")
        else:
            st.caption(f"📡 Using historical volatility — live data unavailable")

        # --- OPTION PRICES ---
        st.markdown("### 💰 Option Prices")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📗 Call Option")
            st.caption("Profits when index goes UP")
            if nse_call and nse_call['lastPrice'] > 0:
                market_price = nse_call['lastPrice']
                bid_price = nse_call.get('bidPrice', 0)
                ask_price = nse_call.get('askPrice', 0)
                mid_price = nse_call.get('midPrice', market_price)
                data_quality = nse_call.get('dataQuality', 'good')
                quality_notes = nse_call.get('qualityNotes', [])

                st.metric(
                    "Last Traded Price",
                    f"₹{market_price:.2f}",
                    help="Last traded price from NSE option chain"
                )
                if bid_price > 0 and ask_price > 0:
                    st.metric(
                        "Bid / Ask",
                        f"₹{bid_price:.2f} / ₹{ask_price:.2f}",
                        help="Current bid and ask — midpoint used for IV calculation"
                    )
                st.metric(
                    "Implied Volatility (NSE)",
                    f"{iv_call*100:.2f}%" if iv_call else "N/A",
                    help="Implied volatility from NSE — calculated directly from exchange data, not circular"
                )
                st.metric(
                    "Open Interest",
                    f"{nse_call['openInterest']:,}",
                    help="Number of outstanding contracts. Higher OI = more liquid."
                )
                st.metric(
                    "Volume",
                    f"{nse_call['volume']:,}",
                    help="Contracts traded today. Low volume may mean stale LTP."
                )
                if data_quality == "poor":
                    st.warning(f"⚠️ Data quality concerns: {', '.join(quality_notes)}")
            else:
                st.info("No market data available for this strike")

        with col2:
            st.markdown("#### 📕 Put Option")
            st.caption("Profits when index goes DOWN")
            if nse_put and nse_put['lastPrice'] > 0:
                market_price_put = nse_put['lastPrice']
                bid_price_put = nse_put.get('bidPrice', 0)
                ask_price_put = nse_put.get('askPrice', 0)
                mid_price_put = nse_put.get('midPrice', market_price_put)
                data_quality_put = nse_put.get('dataQuality', 'good')
                quality_notes_put = nse_put.get('qualityNotes', [])

                st.metric(
                    "Last Traded Price",
                    f"₹{market_price_put:.2f}",
                    help="Last traded price from NSE option chain"
                )
                if bid_price_put > 0 and ask_price_put > 0:
                    st.metric(
                        "Bid / Ask",
                        f"₹{bid_price_put:.2f} / ₹{ask_price_put:.2f}",
                        help="Current bid and ask — midpoint used for IV calculation"
                    )
                st.metric(
                    "Implied Volatility (NSE)",
                    f"{iv_put*100:.2f}%" if iv_put else "N/A",
                    help="Put IV is typically higher than call IV due to market skew — traders pay more for downside protection."
                )
                st.metric(
                    "Open Interest",
                    f"{nse_put['openInterest']:,}",
                    help="Number of outstanding contracts. Higher OI = more liquid."
                )
                st.metric(
                    "Volume",
                    f"{nse_put['volume']:,}",
                    help="Contracts traded today. Low volume may mean stale LTP."
                )
                if data_quality_put == "poor":
                    st.warning(f"⚠️ Data quality concerns: {', '.join(quality_notes_put)}")
            else:
                st.info("No market data available for this strike")

        # --- GREEKS ---
        st.markdown("### 🔢 Greeks")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Delta (Call)", f"{results['delta_call']:.4f}",
                   help="If index moves ₹1 up, call price changes by this amount. Range: 0 to 1.")
        col2.metric("Delta (Put)", f"{results['delta_put']:.4f}",
                   help="If index moves ₹1 up, put price changes by this amount. Range: -1 to 0.")
        col3.metric("Gamma", f"{results['gamma']:.6f}",
                   help="How fast Delta changes when index moves ₹1.")
        col4.metric("Theta/day", f"₹{results['theta_call']:.2f}",
                   help="Your option loses this much value every single day just from time passing.")
        col5.metric("Vega (1%)", f"₹{results['vega']:.2f}",
                   help="If market volatility increases by 1%, option price changes by this amount.")

        st.markdown("---")

        # --- POSITION SIZING ---
        st.markdown("### 🎯 Position Sizing")

        option_premium = nse_call['lastPrice'] if nse_call and nse_call['lastPrice'] > 0 else results['BS_call']
        max_risk_rupees = account_size * (risk_percent / 100)
        cost_per_lot = option_premium * lot_size
        max_lots = int(max_risk_rupees / cost_per_lot) if cost_per_lot > 0 else 0
        total_cost = max_lots * cost_per_lot
        breakeven_price = K + option_premium

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Max Lots", f"{max_lots} lots",
                   help=f"Maximum lots keeping risk at {risk_percent}% of your ₹{account_size:,} account")
        col2.metric("Total Cost", f"₹{total_cost:,.2f}",
                   help="Total premium paid upfront to buy these contracts")
        col3.metric("Max Loss", f"₹{total_cost:,.2f}",
                   help="The most you can ever lose — options buyers cannot lose more than premium paid")
        col4.metric("Breakeven", f"₹{breakeven_price:,.2f}",
                   help="Index must cross this price at expiry for the call to be profitable")

        if max_lots > 0:
            st.success(f"Buy max **{max_lots} lots** — costs ₹{total_cost:,.2f} — max loss ₹{total_cost:,.2f} ({risk_percent}% of ₹{account_size:,})")
        else:
            st.warning(f"Need ₹{cost_per_lot:,.2f} minimum for 1 lot ({(cost_per_lot/account_size*100):.1f}% of account)")

        st.markdown("---")

        # --- TABS ---
        tab1, tab2, tab3 = st.tabs(["📈 Price Paths", "💹 Payoff Diagram", "⚠️ Risk Analysis"])

        with tab1:
            st.caption("Each line = one possible future for the index based on current volatility")
            fig, ax = plt.subplots(figsize=(12, 5))
            ax.plot(results['paths'][:, :100], alpha=0.2, linewidth=0.5)
            ax.axhline(y=K, color='red', linestyle='--', linewidth=2, label=f'Strike ₹{K}')
            ax.axhline(y=S0, color='green', linestyle='--', linewidth=2, label=f'Current ₹{S0}')
            ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
            ax.set_title(f'50,000 Simulated Price Paths')
            ax.set_xlabel('Trading Days')
            ax.set_ylabel(f'{index_name} Price (₹)')
            ax.legend()
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)

        with tab2:
            st.caption("Your exact profit or loss at every possible index price on expiry day")
            nifty_range = np.linspace(S0 * 0.7, S0 * 1.3, 500)
            call_payoff = np.maximum(nifty_range - K, 0) - option_premium
            put_payoff = np.maximum(K - nifty_range, 0) - (nse_put['lastPrice'] if nse_put and nse_put['lastPrice'] > 0 else results['BS_put'])

            fig2, ax2 = plt.subplots(figsize=(12, 5))
            ax2.plot(nifty_range, call_payoff, color='green', linewidth=2, label='Call P&L')
            ax2.plot(nifty_range, put_payoff, color='red', linewidth=2, label='Put P&L')
            ax2.axhline(y=0, color='white', linewidth=1)
            ax2.axvline(x=K, color='yellow', linewidth=1.5, linestyle='--', label=f'Strike ₹{K}')
            ax2.axvline(x=S0, color='cyan', linewidth=1.5, linestyle='--', label=f'Current ₹{S0}')
            ax2.fill_between(nifty_range, call_payoff, 0, where=(call_payoff > 0), color='green', alpha=0.1)
            ax2.fill_between(nifty_range, put_payoff, 0, where=(put_payoff > 0), color='red', alpha=0.1)
            ax2.set_title('Profit & Loss at Expiry')
            ax2.set_xlabel(f'{index_name} Price at Expiry (₹)')
            ax2.set_ylabel('P&L (₹)')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            st.pyplot(fig2)

        with tab3:
            st.caption("Risk metrics calculated from 50,000 simulated market scenarios")
            nifty_returns = (results['final_prices'] - S0) / S0
            var_95 = np.percentile(nifty_returns, 5)
            var_99 = np.percentile(nifty_returns, 1)
            cvar_95 = nifty_returns[nifty_returns <= var_95].mean()

            var_95_rs = abs(var_95 * S0)
            var_99_rs = abs(var_99 * S0)
            cvar_95_rs = abs(cvar_95 * S0)

            call_pnl = np.maximum(results['final_prices'] - K, 0) - option_premium
            put_premium = nse_put['lastPrice'] if nse_put and nse_put['lastPrice'] > 0 else results['BS_put']
            put_pnl = np.maximum(K - results['final_prices'], 0) - put_premium

            st.markdown("#### Index Risk")
            col1, col2, col3 = st.columns(3)
            col1.metric("VaR 95%", f"₹{var_95_rs:.2f}", f"{var_95*100:.2f}%",
                       help="With 95% confidence, the index won't fall more than this by expiry")
            col2.metric("VaR 99%", f"₹{var_99_rs:.2f}", f"{var_99*100:.2f}%",
                       help="Extreme scenario — only 1 in 100 simulated futures is worse than this")
            col3.metric("CVaR 95%", f"₹{cvar_95_rs:.2f}", f"{cvar_95*100:.2f}%",
                       help="In the worst 5% of scenarios, this is the average loss")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 📗 Call Risk")
                st.metric("Max Loss", f"₹{option_premium:.2f}",
                         help="The most you can lose — never more than premium paid")
                st.metric("Max Profit", f"₹{call_pnl.max():.2f}",
                         help="Best case scenario from 50,000 simulations")
                profitable = (call_pnl > 0).sum() / len(call_pnl) * 100
                st.metric("Probability of Profit", f"{profitable:.1f}%",
                         help="What % of 50,000 simulated futures ended with this call profitable at expiry")

            with col2:
                st.markdown("#### 📕 Put Risk")
                st.metric("Max Loss", f"₹{put_premium:.2f}",
                         help="The most you can lose — never more than premium paid")
                st.metric("Max Profit", f"₹{put_pnl.max():.2f}",
                         help="Best case scenario from 50,000 simulations")
                profitable_put = (put_pnl > 0).sum() / len(put_pnl) * 100
                st.metric("Probability of Profit", f"{profitable_put:.1f}%",
                         help="What % of 50,000 simulated futures ended with this put profitable at expiry")

            fig3, ax3 = plt.subplots(figsize=(12, 4))
            ax3.hist(nifty_returns * 100, bins=100, color='blue', alpha=0.6, edgecolor='none')
            ax3.axvline(x=var_95*100, color='orange', linewidth=2,
                        linestyle='--', label=f'VaR 95%: {var_95*100:.2f}%')
            ax3.axvline(x=var_99*100, color='red', linewidth=2,
                        linestyle='--', label=f'VaR 99%: {var_99*100:.2f}%')
            ax3.axvline(x=0, color='white', linewidth=1)
            ax3.set_title('Return Distribution at Expiry')
            ax3.set_xlabel('Return (%)')
            ax3.set_ylabel('Frequency')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            st.pyplot(fig3)

    elif calculate and not S0:
        st.error(f"❌ Unable to fetch {index_name} price. Please try again.")
    else:
        st.markdown("### 👈 Select your option in the sidebar and click Calculate")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("#### 📊 IV Analysis")
            st.markdown("See the implied volatility for any strike — directly from NSE exchange data, not a model calculation.")
        with col2:
            st.markdown("#### ⚠️ Risk Analysis")
            st.markdown("Understand exactly how much you can lose — in rupees — before you trade.")
        with col3:
            st.markdown("#### 🎯 Position Sizing")
            st.markdown("Know exactly how many lots to buy based on your account size and risk tolerance.")

# ============================================================
# PAGE 2 - PORTFOLIO VAR
# ============================================================
elif page == "📊 Portfolio VaR":

    st.markdown("### 📊 Portfolio VaR")
    st.markdown("Add your open positions to see combined risk across your entire portfolio")

    with st.spinner("Fetching market data..."):
        india_vix = get_india_vix()
        rbi_rate = get_rbi_rate()
        S0_nifty = get_nifty_price()
        S0_banknifty = get_banknifty_price()
        S0_finnifty = get_finnifty_price()
        S0_midcap = get_midcap_price()
        sigma_nifty = india_vix if india_vix else get_nifty_volatility()
        weekly_date, weekly_T, weekly_days = get_next_expiry()
        monthly_date, monthly_T, monthly_days = get_monthly_expiry()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Nifty 50", f"₹{S0_nifty:,.2f}" if S0_nifty else "N/A")
    col2.metric("BankNifty", f"₹{S0_banknifty:,.2f}" if S0_banknifty else "N/A")
    col3.metric("FinNifty", f"₹{S0_finnifty:,.2f}" if S0_finnifty else "N/A")
    col4.metric("MidcapNifty", f"₹{S0_midcap:,.2f}" if S0_midcap else "N/A")

    st.markdown("---")

    st.markdown("### ➕ Add Position")

    if 'positions' not in st.session_state:
        st.session_state.positions = []

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        pos_index = st.selectbox("Index", ["Nifty 50", "BankNifty", "FinNifty", "MidcapNifty"], key="pos_index")
    with col2:
        pos_action = st.selectbox("Action", ["Buy", "Sell"], key="pos_action",
                                  help="Buy = paying premium | Sell = receiving premium")
    with col3:
        pos_type = st.selectbox("Type", ["Call", "Put"], key="pos_type",
                               help="Call = profits when index rises | Put = profits when index falls")
    with col4:
        pos_strike = st.number_input("Strike", min_value=5000, max_value=100000,
                                     value=int(S0_nifty) + 500 if S0_nifty else 25000,
                                     step=50, key="pos_strike")
    with col5:
        pos_premium = st.number_input("Premium (₹)", min_value=0.0,
                                      max_value=10000.0, value=100.0,
                                      step=0.5, key="pos_premium",
                                      help="Price you paid (buy) or received (sell) for this contract")
    with col6:
        pos_lots = st.number_input("Lots", min_value=1, max_value=100,
                                   value=1, step=1, key="pos_lots")

    if st.button("➕ Add Position", type="secondary"):
        if pos_index == "Nifty 50":
            lot_size = 65
        elif pos_index == "BankNifty":
            lot_size = 30
        elif pos_index == "FinNifty":
            lot_size = 60
        else:
            lot_size = 120

        st.session_state.positions.append({
            'index': pos_index,
            'action': pos_action.lower(),
            'option_type': pos_type.lower(),
            'strike': pos_strike,
            'premium': pos_premium,
            'lots': pos_lots,
            'lot_size': lot_size
        })
        st.rerun()

    if st.session_state.positions:
        st.markdown("### 📋 Positions")

        for i, pos in enumerate(st.session_state.positions):
            col1, col2 = st.columns([5, 1])
            with col1:
                action_emoji = "🟢" if pos['action'] == 'buy' else "🔴"
                type_emoji = "📗" if pos['option_type'] == 'call' else "📕"
                st.markdown(f"{action_emoji} {type_emoji} **{pos['action'].upper()}** {pos['lots']} lot(s) — {pos['index']} {pos['strike']} {pos['option_type'].upper()} @ ₹{pos['premium']}")
            with col2:
                if st.button("❌", key=f"remove_{i}"):
                    st.session_state.positions.pop(i)
                    st.rerun()

        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("🗑️ Clear All"):
                st.session_state.positions = []
                st.rerun()

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            portfolio_expiry = st.radio("Expiry", ["Weekly", "Monthly"])
        with col2:
            if portfolio_expiry == "Weekly":
                T_portfolio = weekly_T
                days_portfolio = weekly_days
                expiry_str = weekly_date
            else:
                T_portfolio = monthly_T
                days_portfolio = monthly_days
                expiry_str = monthly_date
            st.info(f"📅 {expiry_str} ({days_portfolio} days away)")

        if st.button("📊 Calculate Portfolio VaR", type="primary"):
            if not rbi_rate:
                st.error("❌ Unable to fetch RBI rate. Please try again.")
                st.stop()

            with st.spinner("Running simulation..."):
                portfolio_results = simulate_portfolio_pnl(
                    positions=st.session_state.positions,
                    S0=S0_nifty,
                    sigma=sigma_nifty,
                    T=T_portfolio,
                    r=rbi_rate,
                    paths=50000
                )

            st.markdown("### 📊 Portfolio Risk")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("VaR 95%", f"₹{abs(portfolio_results['var_95']):,.2f}",
                       help="With 95% confidence your total portfolio won't lose more than this by expiry")
            col2.metric("VaR 99%", f"₹{abs(portfolio_results['var_99']):,.2f}",
                       help="Extreme scenario — only 1 in 100 futures is worse than this total loss")
            col3.metric("CVaR 95%", f"₹{abs(portfolio_results['cvar_95']):,.2f}",
                       help="In the worst 5% of scenarios, this is the average total portfolio loss")
            col4.metric("Prob of Profit", f"{portfolio_results['prob_profit']:.1f}%",
                       help="% of 50,000 simulated futures where your entire portfolio ends profitably")

            col1, col2, col3 = st.columns(3)
            col1.metric("Max Profit", f"₹{portfolio_results['max_profit']:,.2f}",
                       help="Best case scenario from 50,000 simulations")
            col2.metric("Max Loss", f"₹{portfolio_results['max_loss']:,.2f}",
                       help="Worst case scenario from 50,000 simulations")
            col3.metric("Expected P&L", f"₹{portfolio_results['avg_pnl']:,.2f}",
                       help="Average P&L across all 50,000 simulated futures")

            fig, ax = plt.subplots(figsize=(12, 4))
            pnl = portfolio_results['total_pnl']
            ax.hist(pnl, bins=100, color='blue', alpha=0.6, edgecolor='none')
            ax.axvline(x=portfolio_results['var_95'], color='orange', linewidth=2,
                      linestyle='--', label=f"VaR 95%: ₹{portfolio_results['var_95']:,.0f}")
            ax.axvline(x=portfolio_results['var_99'], color='red', linewidth=2,
                      linestyle='--', label=f"VaR 99%: ₹{portfolio_results['var_99']:,.0f}")
            ax.axvline(x=0, color='white', linewidth=2, linestyle='-', label='Break Even')
            ax.axvline(x=portfolio_results['avg_pnl'], color='green', linewidth=2,
                      linestyle='--', label=f"Expected: ₹{portfolio_results['avg_pnl']:,.0f}")
            ax.set_title('Portfolio P&L Distribution')
            ax.set_xlabel('P&L (₹)')
            ax.set_ylabel('Frequency')
            ax.legend()
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)

            fig2, ax2 = plt.subplots(figsize=(12, 4))
            price_range = np.linspace(S0_nifty * 0.8, S0_nifty * 1.2, 500)
            total_payoff = np.zeros(len(price_range))

            for pos in st.session_state.positions:
                if pos['option_type'] == 'call':
                    payoff = np.maximum(price_range - pos['strike'], 0)
                else:
                    payoff = np.maximum(pos['strike'] - price_range, 0)

                if pos['action'] == 'buy':
                    pnl = (payoff - pos['premium']) * pos['lots'] * pos['lot_size']
                else:
                    pnl = (pos['premium'] - payoff) * pos['lots'] * pos['lot_size']

                total_payoff += pnl

            ax2.plot(price_range, total_payoff, color='cyan', linewidth=2.5, label='Portfolio P&L')
            ax2.axhline(y=0, color='white', linewidth=1)
            ax2.axvline(x=S0_nifty, color='green', linewidth=1.5,
                       linestyle='--', label=f'Current ₹{S0_nifty:,.0f}')
            ax2.fill_between(price_range, total_payoff, 0,
                            where=(total_payoff > 0), color='green', alpha=0.15)
            ax2.fill_between(price_range, total_payoff, 0,
                            where=(total_payoff < 0), color='red', alpha=0.15)
            ax2.set_title('Portfolio Payoff at Expiry')
            ax2.set_xlabel('Index Price at Expiry (₹)')
            ax2.set_ylabel('P&L (₹)')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            st.pyplot(fig2)

    else:
        st.info("👆 Add your positions above to analyze combined portfolio risk")
        st.markdown("""
            **Try this example:**
            - Buy 1 lot Nifty 24800 CE @ ₹100
            - Sell 1 lot Nifty 25000 CE @ ₹50
        """)

# ============================================================
# PAGE 3 - IV ANALYSIS
# ============================================================
elif page == "🔍 IV Analysis":

    st.markdown("### 🔍 IV Analysis")
    st.markdown("Analyse implied volatility across all strikes — put-call IV divergence and data quality")
    st.caption("ℹ️ IV divergence between calls and puts at the same strike usually reflects bid-ask spread, stale quotes on illiquid strikes, or put-call skew — not mispricing. Always check volume and OI before drawing conclusions.")

    with st.spinner("Fetching market data..."):
        india_vix = get_india_vix()
        rbi_rate = get_rbi_rate()

    col1, col2 = st.columns(2)

    with col1:
        screener_index = st.selectbox(
            "Select Index",
            ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"],
            help="Select the index to analyse"
        )

    with st.spinner("Fetching expiry dates..."):
        expiry_dates = get_expiry_dates_from_supabase(screener_index)

    with col2:
        if expiry_dates:
            selected_expiry = st.selectbox(
                "Select Expiry",
                expiry_dates,
                help="Select expiry date to analyse"
            )
        else:
            st.error("No expiry dates available")
            selected_expiry = None

    if st.button("🔍 Analyse IV", type="primary") and selected_expiry:

        with st.spinner("Fetching option chain..."):
            if screener_index == "NIFTY":
                S0 = get_nifty_price()
            elif screener_index == "BANKNIFTY":
                S0 = get_banknifty_price()
            elif screener_index == "FINNIFTY":
                S0 = get_finnifty_price()
            else:
                S0 = get_midcap_price()

            if not S0:
                st.error("Unable to fetch index price")
                st.stop()

            if not rbi_rate:
                st.error("Unable to fetch RBI rate")
                st.stop()

            all_options = get_all_options_from_supabase(screener_index, selected_expiry)

            if not all_options:
                st.error("No options data available for selected expiry")
                st.stop()

            expiry_dt = datetime.strptime(selected_expiry, "%d-%b-%Y")
            today = datetime.now()
            days_to_expiry = (expiry_dt - today).days
            T = max(days_to_expiry / 252, 0.001)

            # Process options
            strikes_data = {}
            for row in all_options:
                strike = row['strike']
                if strike not in strikes_data:
                    strikes_data[strike] = {'CE': None, 'PE': None}
                strikes_data[strike][row['option_type']] = row

            results_list = []

            for strike, options in strikes_data.items():
                ce = options.get('CE')
                pe = options.get('PE')

                if not ce or not pe:
                    continue

                ce_price = float(ce['last_price'])
                pe_price = float(pe['last_price'])
                ce_volume = int(ce.get('volume', 0))
                pe_volume = int(pe.get('volume', 0))
                ce_oi = int(ce.get('open_interest', 0))
                pe_oi = int(pe.get('open_interest', 0))

                # Use NSE IV directly
                ce_nse_iv = float(ce.get('nse_iv', 0))
                pe_nse_iv = float(pe.get('nse_iv', 0))

                # Bid/ask
                ce_bid = float(ce.get('bid_price', 0))
                ce_ask = float(ce.get('ask_price', 0))
                pe_bid = float(pe.get('bid_price', 0))
                pe_ask = float(pe.get('ask_price', 0))

                if ce_price <= 0 or pe_price <= 0:
                    continue

                # Skip if NSE IV not available
                if ce_nse_iv <= 0 or pe_nse_iv <= 0:
                    continue

                # Data quality flags
                ce_quality = "good"
                pe_quality = "good"

                if ce_volume < 100:
                    ce_quality = "poor"
                if pe_volume < 100:
                    pe_quality = "poor"
                if ce_oi == 0:
                    ce_quality = "poor"
                if pe_oi == 0:
                    pe_quality = "poor"

                # Bid ask spread check
                ce_spread_pct = ((ce_ask - ce_bid) / ce_price * 100) if ce_bid > 0 and ce_ask > 0 and ce_price > 0 else None
                pe_spread_pct = ((pe_ask - pe_bid) / pe_price * 100) if pe_bid > 0 and pe_ask > 0 and pe_price > 0 else None

                if ce_spread_pct and ce_spread_pct > 10:
                    ce_quality = "poor"
                if pe_spread_pct and pe_spread_pct > 10:
                    pe_quality = "poor"

                # IV divergence — put-call IV spread at same strike
                iv_divergence = pe_nse_iv - ce_nse_iv

                # Moneyness
                if strike < S0 * 0.99:
                    moneyness = "ITM"
                elif strike > S0 * 1.01:
                    moneyness = "OTM"
                else:
                    moneyness = "ATM"

                results_list.append({
                    'Strike': int(strike),
                    'Moneyness': moneyness,
                    'Call LTP': round(ce_price, 2),
                    'Call Bid': round(ce_bid, 2) if ce_bid > 0 else '-',
                    'Call Ask': round(ce_ask, 2) if ce_ask > 0 else '-',
                    'Call IV': round(ce_nse_iv, 2),
                    'Call Vol': ce_volume,
                    'Call OI': ce_oi,
                    'Call Quality': ce_quality,
                    'Put LTP': round(pe_price, 2),
                    'Put Bid': round(pe_bid, 2) if pe_bid > 0 else '-',
                    'Put Ask': round(pe_ask, 2) if pe_ask > 0 else '-',
                    'Put IV': round(pe_nse_iv, 2),
                    'Put Vol': pe_volume,
                    'Put OI': pe_oi,
                    'Put Quality': pe_quality,
                    'IV Divergence': round(iv_divergence, 2),
                })

        if results_list:
            df = pd.DataFrame(results_list)
            df = df.sort_values('Strike')

            st.markdown(f"### 📊 IV Analysis — {screener_index} | {selected_expiry} | Spot: ₹{S0:,.2f}")
            st.caption(f"Analysing {len(results_list)} strikes | NSE IV directly from exchange | Only strikes with NSE IV > 0 shown")

            # Summary metrics
            atm_rows = df[df['Moneyness'] == 'ATM']
            if len(atm_rows) > 0:
                atm = atm_rows.iloc[0]
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("ATM Strike", f"₹{atm['Strike']}")
                col2.metric("ATM Call IV", f"{atm['Call IV']:.2f}%",
                           help="At-the-money call implied volatility from NSE")
                col3.metric("ATM Put IV", f"{atm['Put IV']:.2f}%",
                           help="At-the-money put implied volatility from NSE")
                col4.metric("ATM IV Divergence", f"{atm['IV Divergence']:.2f}%",
                           help="Put IV minus Call IV at ATM — should be near zero for liquid strikes")

            st.markdown("---")

            # Gate the divergence signal — only show for liquid strikes
            liquid_df = df[(df['Call Vol'] >= 100) & (df['Put Vol'] >= 100) &
                          (df['Call OI'] > 0) & (df['Put OI'] > 0)]

            st.markdown("#### 📊 Full IV Table")

            def color_quality(val):
                if val == 'poor':
                    return 'color: orange'
                return 'color: green'

            def color_divergence(val):
                if abs(val) > 2:
                    return 'color: orange'
                return 'color: white'

            display_df = df[['Strike', 'Moneyness', 'Call LTP', 'Call IV',
                            'Call Vol', 'Call OI', 'Call Quality',
                            'Put LTP', 'Put IV', 'Put Vol', 'Put OI',
                            'Put Quality', 'IV Divergence']].copy()

            st.dataframe(
                display_df.style
                .applymap(color_quality, subset=['Call Quality', 'Put Quality'])
                .applymap(color_divergence, subset=['IV Divergence']),
                use_container_width=True,
                hide_index=True
            )

            st.markdown("---")

            # Largest IV divergences — gated to liquid strikes only
            st.markdown("#### 📊 Largest Put-Call IV Divergence (Liquid Strikes Only)")
            st.caption("ℹ️ Large divergence on liquid strikes may reflect genuine put-call skew or temporary supply/demand imbalance — not necessarily a trading opportunity.")

            if len(liquid_df) > 0:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Highest Put IV vs Call IV**")
                    top_div = liquid_df.nlargest(5, 'IV Divergence')[
                        ['Strike', 'Call IV', 'Put IV', 'IV Divergence', 'Call Vol', 'Put Vol']
                    ]
                    st.dataframe(top_div, use_container_width=True, hide_index=True)

                with col2:
                    st.markdown("**Lowest Put IV vs Call IV**")
                    bottom_div = liquid_df.nsmallest(5, 'IV Divergence')[
                        ['Strike', 'Call IV', 'Put IV', 'IV Divergence', 'Call Vol', 'Put Vol']
                    ]
                    st.dataframe(bottom_div, use_container_width=True, hide_index=True)
            else:
                st.warning("No liquid strikes found (volume >= 100 for both call and put)")

            # IV Smile chart
            st.markdown("#### 📈 IV Smile")
            st.caption("Call IV and Put IV across strikes — the smile shape reflects market expectations")

            fig, ax = plt.subplots(figsize=(12, 5))
            ax.plot(df['Strike'], df['Call IV'], color='green',
                   linewidth=2, marker='o', markersize=3, label='Call IV')
            ax.plot(df['Strike'], df['Put IV'], color='red',
                   linewidth=2, marker='o', markersize=3, label='Put IV')
            ax.axvline(x=S0, color='cyan', linewidth=1.5,
                      linestyle='--', label=f'Spot ₹{S0:,.0f}')
            ax.set_title(f'IV Smile — {screener_index} {selected_expiry}')
            ax.set_xlabel('Strike Price (₹)')
            ax.set_ylabel('Implied Volatility (%)')
            ax.legend()
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)

        else:
            st.warning("No valid options data found — NSE IV may not be available for selected expiry")