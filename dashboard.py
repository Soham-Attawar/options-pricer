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
        <p>Professional options pricing using Monte Carlo simulation & Black-Scholes model</p>
    </div>
""", unsafe_allow_html=True)

# --- NAVIGATION ---
page = st.radio(
    "Navigation",
    ["🏠 Option Pricer", "📊 Portfolio VaR"],
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("---")

# ============================================================
# PAGE 1 - OPTION PRICER
# ============================================================
if page == "🏠 Option Pricer":

    # --- SIDEBAR PART 1 ---
    with st.sidebar:
        st.markdown("## ⚙️ Configure Option")
        st.markdown("---")

        st.markdown("### 📌 Select Index")
        index_choice = st.radio(
            "Choose Index",
            ["Nifty 50", "BankNifty"],
            help="Nifty 50 expires Tuesday, BankNifty expires last Tuesday of month"
        )
        st.markdown("---")

    # --- FETCH MARKET DATA ---
    with st.spinner("Fetching live market data..."):
        india_vix = get_india_vix()

        if index_choice == "Nifty 50":
            S0 = get_nifty_price()
            sigma_historical = get_nifty_volatility()
            sigma = india_vix if india_vix else sigma_historical
            weekly_date, weekly_T, weekly_days = get_next_expiry()
            monthly_date, monthly_T, monthly_days = get_monthly_expiry()
            index_name = "Nifty 50"
            nse_symbol = "NIFTY"
            lot_size = 65
        else:
            S0 = get_banknifty_price()
            sigma_historical = get_banknifty_volatility()
            sigma = india_vix if india_vix else sigma_historical
            weekly_date, weekly_T, weekly_days = get_banknifty_expiry()
            monthly_date, monthly_T, monthly_days = get_monthly_expiry()
            index_name = "BankNifty"
            nse_symbol = "BANKNIFTY"
            lot_size = 30

    # --- SIDEBAR PART 2 ---
    with st.sidebar:
        st.markdown(f"### 🏦 {index_name}")
        st.markdown(f"## ₹{S0:,.2f}")
        if india_vix:
            st.markdown(f"India VIX: **{india_vix*100:.2f}%** | RBI Rate: **6.5%**")
        else:
            st.markdown(f"Volatility: **{sigma*100:.2f}%** | RBI Rate: **6.5%**")
        st.markdown("---")

        st.markdown("### 📅 Expiry")
        if index_choice == "Nifty 50":
            expiry_options = ["Weekly", "Monthly"]
            expiry_help = "Nifty: Weekly=Tuesday | Monthly=Last Tuesday of month"
        else:
            expiry_options = ["Monthly"]
            expiry_help = "BankNifty: Only monthly expiry available (last Tuesday)"

        expiry_type = st.radio(
            "Select Expiry Type",
            expiry_options,
            help=expiry_help
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

        if index_choice == "Nifty 50":
            strike_min = 15000
            strike_max = 40000
            strike_step = 50
        else:
            strike_min = 40000
            strike_max = 80000
            strike_step = 100

        K = st.number_input(
            "Strike Price (₹)",
            min_value=strike_min,
            max_value=strike_max,
            value=int(suggested_strike),
            step=strike_step,
            help="Enter the option strike price"
        )

        distance = K - S0
        distance_pct = (distance / S0) * 100
        if distance > 0:
            st.markdown(f"📊 Strike is **₹{distance:.0f} ({distance_pct:.1f}%) above** current price")
        else:
            st.markdown(f"📊 Strike is **₹{abs(distance):.0f} ({abs(distance_pct):.1f}%) below** current price")

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
            help="What % of your account are you willing to risk?"
        )

        st.markdown("---")
        calculate = st.button("🚀 Calculate Option Price", type="primary", use_container_width=True)

    # --- LIVE MARKET DATA ---
    st.markdown("### 📊 Live Market Data")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(f"{index_name} Price", f"₹{S0:,.2f}")
    if india_vix:
        col2.metric("India VIX", f"{india_vix*100:.2f}%")
    else:
        col2.metric("Historical Volatility", f"{sigma_historical*100:.2f}%")
    col3.metric("Risk Free Rate (RBI)", "6.5%")
    col4.metric("Days to Expiry", f"{days_remaining} days")

    st.markdown("---")

    if calculate:

        nse_expiry = convert_date_to_nse_format(expiry_date)

        with st.spinner("Fetching live NSE option prices..."):
            nse_call = get_nse_option_price(nse_symbol, K, nse_expiry, "CE")
            nse_put = get_nse_option_price(nse_symbol, K, nse_expiry, "PE")

        with st.spinner("Running Monte Carlo simulation..."):
            r = 0.065

            iv_call = None
            iv_put = None
            data_source = "historical"

            if nse_call and nse_call['lastPrice'] > 0:
                iv_call = calculate_implied_volatility(
                    nse_call['lastPrice'], S0, K, T, r, option_type='call'
                )
                data_source = "live"

            if nse_put and nse_put['lastPrice'] > 0:
                iv_put = calculate_implied_volatility(
                    nse_put['lastPrice'], S0, K, T, r, option_type='put'
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
                vol_source = f"Call IV: {iv_call*100:.2f}% | Put IV: {iv_put*100:.2f}%"
            elif data_source == "live":
                results = price_option(S0, K, T, r=r, sigma=sigma_to_use, paths=paths)
                vol_source = f"IV: {sigma_to_use*100:.2f}%"
            elif data_source == "vix":
                results = price_option(S0, K, T, r=r, sigma=sigma_to_use, paths=paths)
                vol_source = f"India VIX ({india_vix*100:.2f}%) adjusted for skew: {sigma_to_use*100:.2f}%"
            else:
                results = price_option(S0, K, T, r=r, sigma=sigma_to_use, paths=paths)
                vol_source = f"Historical volatility: {sigma_to_use*100:.2f}%"

        # Show data source
        if data_source == "live":
            nse_source = nse_call.get('source', 'live') if nse_call else 'unknown'
            if nse_source == 'supabase':
                updated = nse_call.get('updated_at', '')[:16] if nse_call else ''
                st.info(f"📊 Using Supabase cache — {vol_source} (last updated: {updated})")
            else:
                st.success(f"✅ Live NSE data — {vol_source}")
        elif data_source == "vix":
            st.info(f"📊 {vol_source} (NSE data unavailable)")
        else:
            st.warning(f"⚠️ {vol_source} (NSE data and VIX unavailable)")

        # --- OPTION PRICES ---
        st.markdown("### 💰 Option Prices")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📗 Call Option")
            st.metric("Monte Carlo Price", f"₹{results['call_price']:.2f}")
            st.metric("Black-Scholes Price", f"₹{results['BS_call']:.2f}")
            st.metric("Difference", f"₹{abs(results['BS_call'] - results['call_price']):.2f}")
            if nse_call and nse_call['lastPrice'] > 0:
                st.metric("NSE Market Price", f"₹{nse_call['lastPrice']:.2f}")
                st.metric("OI", f"{nse_call['openInterest']:,}")
                st.metric("Volume", f"{nse_call['volume']:,}")
            if iv_call:
                st.metric("Call IV", f"{iv_call*100:.2f}%")

        with col2:
            st.markdown("#### 📕 Put Option")
            st.metric("Monte Carlo Price", f"₹{results['put_price']:.2f}")
            st.metric("Black-Scholes Price", f"₹{results['BS_put']:.2f}")
            st.metric("Difference", f"₹{abs(results['BS_put'] - results['put_price']):.2f}")
            if nse_put and nse_put['lastPrice'] > 0:
                st.metric("NSE Market Price", f"₹{nse_put['lastPrice']:.2f}")
                st.metric("OI", f"{nse_put['openInterest']:,}")
                st.metric("Volume", f"{nse_put['volume']:,}")
            if iv_put:
                st.metric("Put IV", f"{iv_put*100:.2f}%")

        # --- GREEKS ---
        st.markdown("### 🔢 Greeks")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Delta (Call)", f"{results['delta_call']:.4f}")
        col2.metric("Delta (Put)", f"{results['delta_put']:.4f}")
        col3.metric("Gamma", f"{results['gamma']:.6f}")
        col4.metric("Theta (Call)/day", f"₹{results['theta_call']:.2f}")
        col5.metric("Vega (1% vol)", f"₹{results['vega']:.2f}")

        st.markdown("---")

        # --- POSITION SIZING ---
        st.markdown("### 🎯 Position Sizing Calculator")
        st.markdown("*How many lots should you buy based on your risk tolerance?*")

        option_premium = nse_call['lastPrice'] if nse_call and nse_call['lastPrice'] > 0 else results['call_price']
        max_risk_rupees = account_size * (risk_percent / 100)
        cost_per_lot = option_premium * lot_size
        max_lots = int(max_risk_rupees / cost_per_lot) if cost_per_lot > 0 else 0
        total_cost = max_lots * cost_per_lot
        breakeven_price = K + option_premium

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Max Lots to Buy", f"{max_lots} lots")
        col2.metric("Total Premium Cost", f"₹{total_cost:,.2f}")
        col3.metric("Max Loss", f"₹{total_cost:,.2f}", f"{risk_percent}% of account")
        col4.metric("Breakeven Price", f"₹{breakeven_price:,.2f}")

        if max_lots > 0:
            st.success(f"✅ Buy maximum **{max_lots} lots** of {index_name} {K} CE — Total cost ₹{total_cost:,.2f} — Max loss ₹{total_cost:,.2f} ({risk_percent}% of your ₹{account_size:,} account)")
        else:
            st.warning(f"⚠️ Need at least ₹{cost_per_lot:,.2f} ({(cost_per_lot/account_size*100):.1f}% of account) for 1 lot.")

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
            4. Set your account size and risk tolerance
            5. Click Calculate — live NSE prices fetched automatically
            6. View pricing, Greeks, position sizing, payoff diagram and risk analysis
        """)

# ============================================================
# PAGE 2 - PORTFOLIO VAR
# ============================================================
elif page == "📊 Portfolio VaR":

    st.markdown("### 📊 Portfolio VaR — Combined Risk Analysis")
    st.markdown("Add multiple option positions to see your total portfolio risk")

    # --- FETCH MARKET DATA FOR PORTFOLIO PAGE ---
    with st.spinner("Fetching market data..."):
        india_vix = get_india_vix()
        S0_nifty = get_nifty_price()
        S0_banknifty = get_banknifty_price()
        sigma_nifty = india_vix if india_vix else get_nifty_volatility()
        sigma_banknifty = india_vix if india_vix else get_banknifty_volatility()
        weekly_date, weekly_T, weekly_days = get_next_expiry()
        monthly_date, monthly_T, monthly_days = get_monthly_expiry()

    # Show current prices
    col1, col2, col3 = st.columns(3)
    col1.metric("Nifty 50", f"₹{S0_nifty:,.2f}")
    col2.metric("BankNifty", f"₹{S0_banknifty:,.2f}")
    col3.metric("India VIX", f"{india_vix*100:.2f}%" if india_vix else "N/A")

    st.markdown("---")

    # --- ADD POSITIONS ---
    st.markdown("### ➕ Add Positions")

    # Initialize positions in session state
    if 'positions' not in st.session_state:
        st.session_state.positions = []

    # Position input form
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        pos_index = st.selectbox("Index", ["Nifty 50", "BankNifty"], key="pos_index")
    with col2:
        pos_action = st.selectbox("Action", ["Buy", "Sell"], key="pos_action")
    with col3:
        pos_type = st.selectbox("Type", ["Call", "Put"], key="pos_type")
    with col4:
        pos_strike = st.number_input("Strike", min_value=15000, max_value=80000,
                                     value=int(S0_nifty) + 500, step=50, key="pos_strike")
    with col5:
        pos_premium = st.number_input("Premium (₹)", min_value=0.0,
                                      max_value=10000.0, value=100.0,
                                      step=0.5, key="pos_premium")
    with col6:
        pos_lots = st.number_input("Lots", min_value=1, max_value=100,
                                   value=1, step=1, key="pos_lots")

    if st.button("➕ Add Position", type="secondary"):
        lot_size = 65 if pos_index == "Nifty 50" else 30
        st.session_state.positions.append({
            'index': pos_index,
            'action': pos_action.lower(),
            'option_type': pos_type.lower(),
            'strike': pos_strike,
            'premium': pos_premium,
            'lots': pos_lots,
            'lot_size': lot_size
        })
        st.success(f"Added: {pos_action} {pos_lots} lot(s) of {pos_index} {pos_strike} {pos_type} @ ₹{pos_premium}")
        st.rerun()

    # --- SHOW CURRENT POSITIONS ---
    if st.session_state.positions:
        st.markdown("### 📋 Current Positions")

        for i, pos in enumerate(st.session_state.positions):
            col1, col2 = st.columns([5, 1])
            with col1:
                action_emoji = "🟢" if pos['action'] == 'buy' else "🔴"
                type_emoji = "📗" if pos['option_type'] == 'call' else "📕"
                st.markdown(f"{action_emoji} {type_emoji} **{pos['action'].upper()}** {pos['lots']} lot(s) — {pos['index']} {pos['strike']} {pos['option_type'].upper()} @ ₹{pos['premium']} (lot size: {pos['lot_size']})")
            with col2:
                if st.button("❌", key=f"remove_{i}"):
                    st.session_state.positions.pop(i)
                    st.rerun()

        # Clear all button
        if st.button("🗑️ Clear All Positions"):
            st.session_state.positions = []
            st.rerun()

        st.markdown("---")

        # --- EXPIRY SELECTION ---
        st.markdown("### 📅 Select Expiry for Analysis")
        col1, col2 = st.columns(2)
        with col1:
            portfolio_expiry = st.radio(
                "Expiry",
                ["Weekly", "Monthly"],
                help="Select expiry to analyze portfolio risk against"
            )
        with col2:
            r = 0.065
            if portfolio_expiry == "Weekly":
                T_portfolio = weekly_T
                days_portfolio = weekly_days
                expiry_str = weekly_date
            else:
                T_portfolio = monthly_T
                days_portfolio = monthly_days
                expiry_str = monthly_date

            st.info(f"📅 {expiry_str} ({days_portfolio} days away)")

        # --- CALCULATE PORTFOLIO VAR ---
        if st.button("📊 Calculate Portfolio VaR", type="primary"):
            with st.spinner("Running portfolio simulation..."):
                # Use Nifty as base for now
                # Future: handle mixed Nifty + BankNifty portfolios
                portfolio_results = simulate_portfolio_pnl(
                    positions=st.session_state.positions,
                    S0=S0_nifty,
                    sigma=sigma_nifty,
                    T=T_portfolio,
                    r=r,
                    paths=50000
                )

            # --- RESULTS ---
            st.markdown("### 📊 Portfolio Risk Metrics")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("VaR 95%", f"₹{abs(portfolio_results['var_95']):,.2f}",
                       help="Max loss with 95% confidence")
            col2.metric("VaR 99%", f"₹{abs(portfolio_results['var_99']):,.2f}",
                       help="Max loss with 99% confidence")
            col3.metric("CVaR 95%", f"₹{abs(portfolio_results['cvar_95']):,.2f}",
                       help="Average loss in worst 5% scenarios")
            col4.metric("Prob of Profit", f"{portfolio_results['prob_profit']:.1f}%",
                       help="Probability portfolio is profitable at expiry")

            col1, col2, col3 = st.columns(3)
            col1.metric("Max Profit", f"₹{portfolio_results['max_profit']:,.2f}")
            col2.metric("Max Loss", f"₹{portfolio_results['max_loss']:,.2f}")
            col3.metric("Expected P&L", f"₹{portfolio_results['avg_pnl']:,.2f}")

            # --- PORTFOLIO P&L DISTRIBUTION ---
            st.markdown("### 📈 Portfolio P&L Distribution")
            fig, ax = plt.subplots(figsize=(12, 5))

            pnl = portfolio_results['total_pnl']
            ax.hist(pnl, bins=100, color='blue', alpha=0.6, edgecolor='none')
            ax.axvline(x=portfolio_results['var_95'], color='orange', linewidth=2,
                      linestyle='--', label=f"VaR 95%: ₹{portfolio_results['var_95']:,.0f}")
            ax.axvline(x=portfolio_results['var_99'], color='red', linewidth=2,
                      linestyle='--', label=f"VaR 99%: ₹{portfolio_results['var_99']:,.0f}")
            ax.axvline(x=0, color='white', linewidth=2, linestyle='-', label='Break Even')
            ax.axvline(x=portfolio_results['avg_pnl'], color='green', linewidth=2,
                      linestyle='--', label=f"Expected P&L: ₹{portfolio_results['avg_pnl']:,.0f}")

            ax.set_title('Portfolio P&L Distribution at Expiry')
            ax.set_xlabel('Portfolio P&L (₹)')
            ax.set_ylabel('Frequency')
            ax.legend()
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)

            # --- PORTFOLIO PAYOFF DIAGRAM ---
            st.markdown("### 💹 Portfolio Payoff at Expiry")
            fig2, ax2 = plt.subplots(figsize=(12, 5))

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

            ax2.plot(price_range, total_payoff, color='cyan', linewidth=2.5,
                    label='Portfolio P&L')
            ax2.axhline(y=0, color='white', linewidth=1)
            ax2.axvline(x=S0_nifty, color='green', linewidth=1.5,
                       linestyle='--', label=f'Current ₹{S0_nifty:,.0f}')
            ax2.fill_between(price_range, total_payoff, 0,
                            where=(total_payoff > 0), color='green', alpha=0.15)
            ax2.fill_between(price_range, total_payoff, 0,
                            where=(total_payoff < 0), color='red', alpha=0.15)
            ax2.set_title('Portfolio Payoff at Expiry')
            ax2.set_xlabel('Nifty Price at Expiry (₹)')
            ax2.set_ylabel('Portfolio P&L (₹)')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            st.pyplot(fig2)

    else:
        st.info("👆 Add at least one position above to calculate Portfolio VaR")
        st.markdown("""
            **Example portfolio to try:**
            - Buy 1 lot Nifty 24800 CE @ ₹100 (Long Call)
            - Sell 1 lot Nifty 25000 CE @ ₹50 (Short Call)
            
            This is a **Bull Call Spread** — limited risk, limited reward.
            Portfolio VaR will show your combined risk across both positions.
        """)