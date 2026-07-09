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
get_market_status = market_data.get_market_status
get_rbi_rate = market_data.get_rbi_rate
get_finnifty_price = market_data.get_finnifty_price
get_finnifty_volatility = market_data.get_finnifty_volatility
get_finnifty_expiry = market_data.get_finnifty_expiry
get_midcap_price = market_data.get_midcap_price
get_midcap_volatility = market_data.get_midcap_volatility
get_midcap_expiry = market_data.get_midcap_expiry

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
        <p>Professional options pricing with live NSE data & risk analysis</p>
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

    # --- FETCH MARKET DATA ---
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
        else:  # MidcapNifty
            S0 = get_midcap_price()
            sigma_historical = get_midcap_volatility()
            sigma = india_vix if india_vix else sigma_historical
            weekly_date, weekly_T, weekly_days = get_midcap_expiry()
            monthly_date, monthly_T, monthly_days = get_monthly_expiry()
            index_name = "MidcapNifty"
            nse_symbol = "MIDCPNIFTY"
            lot_size = 120

    # --- SIDEBAR PART 2 ---
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
            else:  # MidcapNifty
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
            st.caption("Profit when index goes UP")
            if nse_call and nse_call['lastPrice'] > 0:
                market_price = nse_call['lastPrice']
                theo_price = results['BS_call']
                diff = theo_price - market_price

                st.metric("Market Price", f"₹{market_price:.2f}",
                         help="Actual last traded price from NSE option chain")
                st.metric("Fair Value", f"₹{theo_price:.2f}",
                         help="Theoretical price calculated using Black-Scholes formula")

                if abs(diff) <= 3:
                    st.success(f"✅ Fairly priced")
                elif diff > 3:
                    st.info(f"📉 Underpriced by ₹{diff:.2f}")
                else:
                    st.warning(f"📈 Overpriced by ₹{abs(diff):.2f}")

                st.metric("Implied Volatility", f"{iv_call*100:.2f}%" if iv_call else "N/A",
                         help="The volatility the market is currently pricing in for this option")
                st.metric("Open Interest", f"{nse_call['openInterest']:,}",
                         help="Number of outstanding contracts. Higher OI = more liquid")
            else:
                st.metric("Fair Value", f"₹{results['BS_call']:.2f}")

        with col2:
            st.markdown("#### 📕 Put Option")
            st.caption("Profit when index goes DOWN")
            if nse_put and nse_put['lastPrice'] > 0:
                market_price_put = nse_put['lastPrice']
                theo_price_put = results['BS_put']
                diff_put = theo_price_put - market_price_put

                st.metric("Market Price", f"₹{market_price_put:.2f}",
                         help="Actual last traded price from NSE option chain")
                st.metric("Fair Value", f"₹{theo_price_put:.2f}",
                         help="Theoretical price calculated using Black-Scholes formula")

                if abs(diff_put) <= 3:
                    st.success(f"✅ Fairly priced")
                elif diff_put > 3:
                    st.info(f"📉 Underpriced by ₹{diff_put:.2f}")
                else:
                    st.warning(f"📈 Overpriced by ₹{abs(diff_put):.2f}")

                st.metric("Implied Volatility", f"{iv_put*100:.2f}%" if iv_put else "N/A",
                         help="Put IV is typically higher than call IV due to market skew")
                st.metric("Open Interest", f"{nse_put['openInterest']:,}",
                         help="Number of outstanding contracts. Higher OI = more liquid")
            else:
                st.metric("Fair Value", f"₹{results['BS_put']:.2f}")

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
            call_payoff = np.maximum(nifty_range - K, 0) - results['BS_call']
            put_payoff = np.maximum(K - nifty_range, 0) - results['BS_put']

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

            call_pnl = np.maximum(results['final_prices'] - K, 0) - results['BS_call']
            put_pnl = np.maximum(K - results['final_prices'], 0) - results['BS_put']

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
                st.metric("Max Loss", f"₹{results['BS_call']:.2f}",
                         help="The most you can lose — never more than premium paid")
                st.metric("Max Profit", f"₹{call_pnl.max():.2f}",
                         help="Best case scenario from 50,000 simulations")
                profitable = (call_pnl > 0).sum() / len(call_pnl) * 100
                st.metric("Probability of Profit", f"{profitable:.1f}%",
                         help="What % of 50,000 simulated futures ended with this call profitable")

            with col2:
                st.markdown("#### 📕 Put Risk")
                st.metric("Max Loss", f"₹{results['BS_put']:.2f}",
                         help="The most you can lose — never more than premium paid")
                st.metric("Max Profit", f"₹{put_pnl.max():.2f}",
                         help="Best case scenario from 50,000 simulations")
                profitable_put = (put_pnl > 0).sum() / len(put_pnl) * 100
                st.metric("Probability of Profit", f"{profitable_put:.1f}%",
                         help="What % of 50,000 simulated futures ended with this put profitable")

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
            st.markdown("#### 📊 Fair Value")
            st.markdown("See if an option is overpriced or underpriced compared to its theoretical fair value.")
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