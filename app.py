"""
====================================================
  AI Personal Wealth Analyzer — Streamlit App
  Run: streamlit run app.py
  Requires: finance_model.pkl in same folder
====================================================
"""

import streamlit as st
import numpy as np
import pandas as pd
import pickle
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import time
import json
import os
from datetime import datetime

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="AI Personal Wealth Analyzer",
    layout="wide"
)

# ============================================================
# GLOBAL CSS
# ============================================================
st.markdown("""
<style>
.section-title {
    background: linear-gradient(90deg, #0f2027, #2c5364);
    color: white;
    padding: 10px 20px;
    border-radius: 10px;
    font-size: 20px;
    font-weight: bold;
    margin-bottom: 15px;
    letter-spacing: 0.5px;
}
.kpi {
    background: linear-gradient(135deg, #2c5364, #0f2027);
    padding: 25px;
    border-radius: 15px;
    color: white;
    text-align: center;
    font-size: 22px;
    font-weight: bold;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.3);
}
.info-card {
    background: #1e293b;
    border-left: 5px solid #38bdf8;
    padding: 15px 20px;
    border-radius: 8px;
    color: #e2e8f0;
    margin: 8px 0;
    font-size: 15px;
}
.loan-card {
    background: #0f172a;
    border: 1px solid #334155;
    padding: 12px 18px;
    border-radius: 10px;
    color: #cbd5e1;
    margin: 5px 0;
    font-size: 14px;
}
.pred-card {
    background: #0f172a;
    border: 1px solid #38bdf8;
    padding: 14px 18px;
    border-radius: 10px;
    color: #e2e8f0;
    margin: 6px 0;
    font-size: 14px;
}
.alert-gain {
    background: #052e16;
    border-left: 5px solid #22c55e;
    padding: 14px 18px;
    border-radius: 10px;
    color: #bbf7d0;
    margin: 6px 0;
    font-size: 15px;
}
.alert-loss {
    background: #2d0a0a;
    border-left: 5px solid #ef4444;
    padding: 14px 18px;
    border-radius: 10px;
    color: #fecaca;
    margin: 6px 0;
    font-size: 15px;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# HELPER — renders a styled section title
# ============================================================
def section(icon, title):
    st.markdown(f'<div class="section-title">{icon} {title}</div>', unsafe_allow_html=True)


# ============================================================
# SMART RUPEE FORMATTER
# Format: K = thousands, L = lakhs, Cr = crores
# ============================================================
def fmt(amount):
    """Format a rupee amount into K / L / Cr for readability."""
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return "Rs. 0"
    neg = amount < 0
    a   = abs(amount)
    if a >= 1_00_00_000:          # 1 crore+
        s = f"Rs. {a / 1_00_00_000:.2f} Cr"
    elif a >= 1_00_000:           # 1 lakh+
        s = f"Rs. {a / 1_00_000:.2f} L"
    elif a >= 1_000:              # 1 thousand+
        s = f"Rs. {a / 1_000:.1f} K"
    else:
        s = f"Rs. {a:,.0f}"
    return f"-{s}" if neg else s


# ============================================================
# LOAD MODEL
# ============================================================
@st.cache_resource
def load_model():
    return pickle.load(open("finance_model.pkl", "rb"))

model = load_model()


# ============================================================
# HISTORY HELPERS
# ============================================================
HISTORY_FILE = "analysis_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_history(data):
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ============================================================
# APP HEADER
# ============================================================
st.markdown("""
<div style='text-align:center; padding:30px 0 10px 0;'>
    <h1 style='font-size:42px; color:#38bdf8;'> AI Personal Wealth Analyzer</h1>
    <p style='color:#94a3b8; font-size:17px;'>
    </p>
</div>
""", unsafe_allow_html=True)
st.divider()


# ============================================================
# SECTION — INCOME INFORMATION
# ============================================================
section("", "Income Information")

c1, c2, c3 = st.columns(3)
with c1:
    income = st.number_input("Monthly Salary (Rs.)", min_value=0, value=0, step=1000)
with c2:
    extra_income = st.number_input("Extra Income (Rs.)", min_value=0, value=0, step=500)
with c3:
    savings = st.number_input("Current Savings (Rs.)", min_value=0, value=0, step=1000)

total_income = income + extra_income

if total_income > 0:
    st.info(f"Total Monthly Income: {fmt(total_income)}")

st.divider()


# ============================================================
# SECTION — LOAN INFORMATION
# ============================================================
section("", "Loan Information")

if "loans" not in st.session_state:
    st.session_state.loans = []

if st.button("Add Loan"):
    st.session_state.loans.append({"name": "", "emi": 0, "principal": 0, "months": 0})

loan_data = []

for i in range(len(st.session_state.loans)):
    st.markdown(f"**Loan {i + 1}**")
    c1, c2, c3, c4 = st.columns(4)
    name      = c1.text_input("Loan Name",             key=f"name{i}", placeholder="e.g. Home Loan")
    emi       = c2.number_input("Monthly EMI (Rs.)",   min_value=0,    key=f"emi{i}")
    principal = c3.number_input("Principal Left (Rs.)", min_value=0,   key=f"principal{i}")
    months    = c4.number_input("Months Remaining",    min_value=0,    key=f"months{i}")
    loan_data.append({"name": name, "emi": emi, "principal": principal, "months": months})

df_loans = pd.DataFrame(loan_data) if loan_data else pd.DataFrame(
    columns=["name", "emi", "principal", "months"]
)

st.divider()


# ============================================================
# ANALYZE BUTTON
# ============================================================
_, mid_col, _ = st.columns([1, 2, 1])
with mid_col:
    if st.button("Analyze My Financial Health", use_container_width=True):
        st.session_state.analyzed = True

if "analyzed" not in st.session_state:
    st.session_state.analyzed = False


# ============================================================
# FULL ANALYSIS
# ============================================================
if st.session_state.analyzed:

    # Core values
    total_emi      = int(df_loans["emi"].sum())       if not df_loans.empty else 0
    principal_left = int(df_loans["principal"].sum()) if not df_loans.empty else 0
    months_left    = int(df_loans["months"].max())    if not df_loans.empty else 0
    loan_count     = len(df_loans)
    balance        = total_income - total_emi
    monthly_balance = balance

    st.divider()

    # ----------------------------------------------------------
    # FINANCIAL OVERVIEW — KPI Dashboard
    # ----------------------------------------------------------
    section("", "Financial Overview")

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="kpi">Income<br>{fmt(total_income)}</div>',   unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi">Total EMI<br>{fmt(total_emi)}</div>',   unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi">Balance<br>{fmt(balance)}</div>',        unsafe_allow_html=True)
    c4.markdown(f'<div class="kpi">Loans<br>{loan_count}</div>',            unsafe_allow_html=True)

    st.divider()

    # ----------------------------------------------------------
    # AI FINANCIAL STRESS PREDICTION
    # ----------------------------------------------------------
    section("", "AI Financial Stress Prediction")

    input_data = np.array([[income, extra_income, loan_count, total_emi, principal_left, months_left, savings]])
    pred = model.predict(input_data)

    bar = st.progress(0, text="Analyzing with AI model...")
    for i in range(100):
        time.sleep(0.008)
        bar.progress(i + 1, text=f"Analyzing... {i+1}%")
    bar.empty()

    if pred[0] == 0:
        st.success("Low Financial Stress")
    elif pred[0] == 1:
        st.warning("Moderate Financial Stress")
    else:
        st.error("High Financial Stress")

    st.divider()

    # ----------------------------------------------------------
    # DEBT RISK SCORE
    # ----------------------------------------------------------
    section("", "Debt Risk Score")

    risk_score = min(int((total_emi / max(total_income, 1)) * 100), 100)

    fig_gauge = go.Figure(go.Indicator(
        mode  = "gauge+number+delta",
        value = risk_score,
        title = {"text": "EMI-to-Income Risk %", "font": {"size": 18}},
        delta = {"reference": 40,
                 "increasing": {"color": "red"},
                 "decreasing": {"color": "green"}},
        gauge = {
            "axis":      {"range": [0, 100], "tickwidth": 1},
            "bar":       {"color": "crimson"},
            "steps":     [
                {"range": [0,  35], "color": "#22c55e"},
                {"range": [35, 60], "color": "#eab308"},
                {"range": [60,100], "color": "#ef4444"},
            ],
            "threshold": {"line": {"color": "white", "width": 3}, "value": 40}
        }
    ))
    fig_gauge.update_layout(height=300, margin=dict(t=50, b=0))
    st.plotly_chart(fig_gauge, use_container_width=True)

    if risk_score <= 35:
        st.success(f"Healthy — EMI is {risk_score}% of income (Safe zone is 35% or below)")
    elif risk_score <= 60:
        st.warning(f"Moderate — EMI is {risk_score}% of income (Caution zone 35–60%)")
    else:
        st.error(f"Danger — EMI is {risk_score}% of income (Critical above 60%)")

    st.divider()

    # ----------------------------------------------------------
    # FUTURE BALANCE PROJECTION
    # ----------------------------------------------------------
    section("", "Future Balance Prediction")

    years        = st.slider("Prediction Years", 1, 10, 3)
    months_total = years * 12
    cumulative   = float(savings)
    projection   = []

    for m in range(1, months_total + 1):
        cumulative += monthly_balance
        projection.append({"Month": m, "Prediction Balance (Rs.)": cumulative})

    df_proj  = pd.DataFrame(projection)
    fig_proj = px.area(
        df_proj, x="Month", y="Prediction Balance (Rs.)",
        color_discrete_sequence=["#38bdf8"],
        title=f"Balance Prediction over {years} Year(s)"
    )
    fig_proj.update_layout(
        plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
        font_color="white", height=350
    )
    st.plotly_chart(fig_proj, use_container_width=True)

    total_gain = monthly_balance * months_total
    if monthly_balance >= 0:
        st.success(
            f"SAFE ZONE — Saving {fmt(monthly_balance)}/month — "
            f"{fmt(total_gain)} total in {years} year(s)"
        )
    else:
        st.error(
            f"DANGER ZONE — Deficit {fmt(abs(monthly_balance))}/month — "
            f"Debt grows {fmt(abs(total_gain))} in {years} year(s)"
        )

    st.divider()

    # ----------------------------------------------------------
    # SECTION 1 — ADDITIONAL PAYMENT SIMULATOR (UPDATED)
    # ----------------------------------------------------------
    section("", "Additional Payment Simulator")

    sim_years     = st.slider("Simulation Period (Years)", 1, 10, 3, key="sim_years")
    sim_months    = sim_years * 12
    extra_payment = st.slider("Extra Monthly Payment Toward EMI (Rs.)", 0, 200000, 0, step=500)

    if total_emi > 0 and principal_left > 0:

        # Amortization — WITHOUT extra payment
        normal_months = 0
        bal = float(principal_left)
        while bal > 0 and normal_months < 99999:
            bal -= total_emi
            normal_months += 1

        # Amortization — WITH extra payment
        new_monthly  = total_emi + extra_payment
        extra_months = 0
        bal2         = float(principal_left)
        while bal2 > 0 and extra_months < 99999:
            bal2 -= new_monthly
            extra_months += 1

        months_saved = max(0, normal_months - extra_months)

        # ── Row 1: Loan Close Time | Time Saved ──
        c1, c2 = st.columns(2)
        c1.metric(
            "Loan Close Time (With Extra Pay)",
            f"{extra_months} months",
            delta=f"-{months_saved} months saved",
            delta_color="inverse"
        )
        c2.metric("Time Saved", f"{months_saved} months")

        # ── Row 2: Time Saved Amount — EMI freed + income kept ──
        time_saved_emi_amount    = months_saved * total_emi
        time_saved_income_amount = months_saved * total_income

        ts1, ts2 = st.columns(2)
        ts1.metric(
            "Time Saved — EMI Amount Freed",
            fmt(time_saved_emi_amount),
            help="Total EMI payments you avoid due to early closure"
        )
        ts2.metric(
            "Time Saved — Income You Keep",
            fmt(time_saved_income_amount),
            help="Total income in hand during months saved by closing early"
        )

        # ── Simulation: month-by-month balance — Normal vs Extra Pay ──
        sim_rows        = []
        bal_normal      = float(savings)
        bal_extra_path  = float(savings)
        loan_bal_normal = float(principal_left)
        loan_bal_extra  = float(principal_left)

        for m in range(1, sim_months + 1):
            # Normal path
            if loan_bal_normal > 0:
                loan_bal_normal = max(loan_bal_normal - total_emi, 0)
                bal_normal     += (total_income - total_emi)
            else:
                bal_normal += total_income  # loan done, full income kept

            # Extra payment path
            if loan_bal_extra > 0:
                pay_this_month  = min(new_monthly, loan_bal_extra)
                loan_bal_extra  = max(loan_bal_extra - new_monthly, 0)
                bal_extra_path += (total_income - pay_this_month)
            else:
                bal_extra_path += total_income  # loan done, full income kept

            sim_rows.append({
                "Month":                   m,
                "Balance Without Extra":   round(bal_normal, 0),
                "Balance With Extra Pay":  round(bal_extra_path, 0),
            })

        df_sim = pd.DataFrame(sim_rows)

        final_normal = df_sim["Balance Without Extra"].iloc[-1]
        final_extra  = df_sim["Balance With Extra Pay"].iloc[-1]
        balance_diff = final_extra - final_normal

        # ── DEBT AVOIDED — actual money saved = balance gained by extra pay ──
        # Debt avoided = what you would have paid in interest/EMI but won't
        debt_avoided = max(
            0,
            (total_emi * normal_months) - (new_monthly * extra_months) - principal_left
        )
        # Real balance gain = what you actually accumulate extra in your hand
        real_balance_gain = balance_diff  # from simulation

        st.markdown(f"**Balance Accumulation Over {sim_years} Year(s) — Normal vs Extra Payment**")

        fig_sim = px.line(
            df_sim, x="Month",
            y=["Balance Without Extra", "Balance With Extra Pay"],
            title=f"Balance Comparison Over {sim_years} Year(s)",
            color_discrete_map={
                "Balance Without Extra":  "#94a3b8",
                "Balance With Extra Pay": "#38bdf8",
            }
        )
        fig_sim.update_layout(
            plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
            font_color="white", height=340
        )
        st.plotly_chart(fig_sim, use_container_width=True)

        # ── KPI row: Balance Normal | Balance Extra | Debt Avoided (balance gain) ──
        ba1, ba2, ba3 = st.columns(3)
        ba1.metric(f"Balance After {sim_years}Y (Normal)",    fmt(final_normal))
        ba2.metric(f"Balance After {sim_years}Y (Extra Pay)", fmt(final_extra))
        ba3.metric(
            "Debt Avoided (Extra Balance Gained)",
            fmt(real_balance_gain),
            delta=fmt(real_balance_gain),
            delta_color="normal",
            help=(
                f"By paying extra, you close {months_saved} months early. "
                f"Those freed months mean your balance is {fmt(real_balance_gain)} "
                f"higher than without extra payment. Interest/excess saved: {fmt(debt_avoided)}."
            )
        )

        if extra_payment > 0:
            sign = "📈 GAIN" if real_balance_gain >= 0 else "📉 LOSS"
            st.info(
                f"{sign} — Extra {fmt(extra_payment)}/month closes loan {months_saved} months early | "
                f"EMI freed: {fmt(time_saved_emi_amount)} | "
                f"Balance gained vs normal path: {fmt(real_balance_gain)} over {sim_years} yr(s)"
            )
    else:
        st.info("Add at least one loan with EMI and Principal to simulate additional payments.")

    st.divider()

    # ----------------------------------------------------------
    # SECTION 2 — LOAN CLOSE ADVICE
    # ----------------------------------------------------------
    section("", "Loan Close Advice")

    if not df_loans.empty and total_income > 0:
        daily_spend        = total_income / 30
        family_expenses    = total_income * 0.40
        personal_lifestyle = total_income * 0.15
        required_total     = total_emi + family_expenses + personal_lifestyle
        extra_needed       = max(0, required_total - total_income)

        c1, c2, c3 = st.columns(3)
        c1.metric("Current Total EMI",          fmt(total_emi))
        c2.metric("Daily Spend (monthly basis)", f"{fmt(daily_spend)} per day")
        c3.metric("Extra Needed to Manage",      f"{fmt(extra_needed)} per month")

        st.markdown("**Monthly Budget Required to Manage Smoothly:**")
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("EMI Payments",    fmt(total_emi))
        b2.metric("Family (40%)",    fmt(family_expenses))
        b3.metric("Lifestyle (15%)", fmt(personal_lifestyle))
        b4.metric("Total Required",  fmt(required_total))

        if extra_needed > 0:
            st.error(f"You need {fmt(extra_needed)} more per month to cover all obligations smoothly.")
        else:
            st.success("Your income comfortably covers EMI, family needs, and lifestyle.")

        top_loans = df_loans[df_loans["emi"] > 0].sort_values("emi", ascending=False)
        if not top_loans.empty:
            t = top_loans.iloc[0]
            st.warning(f"Close '{t['name']}' first — EMI relief of {fmt(t['emi'])} per month")
    else:
        st.info("Add loan and income data to see advice.")

    st.divider()

    # ----------------------------------------------------------
    # SECTION 3 — NET WORTH ANALYSIS (UPDATED)
    # ----------------------------------------------------------
    section("", "Net Worth Analysis")

    annual_income       = total_income * 12
    emi_paid_1year      = total_emi * 12
    principal_after_1yr = max(principal_left - emi_paid_1year, 0)
    balance_after_1yr   = savings + (monthly_balance * 12)
    net_gain_loss       = balance_after_1yr - savings
    current_networth    = savings - principal_left
    future_savings      = savings + monthly_balance * months_total
    future_networth     = future_savings - principal_left

    st.markdown("**1-Year Financial Summary:**")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total 1-Year Income",  fmt(annual_income))
    c2.metric("EMI Paid in 1 Year",   fmt(emi_paid_1year))
    c3.metric("Balance After 1 Year", fmt(balance_after_1yr))
    c4.metric("Net Gain / Loss",      fmt(net_gain_loss),
              delta=fmt(net_gain_loss), delta_color="normal")

    st.markdown("**Long-Term Net Worth (Principal Debt Included):**")
    n1, n2, n3 = st.columns(3)
    n1.metric(
        "Current Net Worth",
        fmt(current_networth),
        help=f"Savings {fmt(savings)} minus Principal Debt {fmt(principal_left)}"
    )
    n2.metric(
        "Net Worth After 1 Year",
        fmt(savings - principal_after_1yr),
        help=f"Principal remaining after 1 year: {fmt(principal_after_1yr)}"
    )
    n3.metric(
        f"Net Worth After {years} Years",
        fmt(future_networth),
        help=f"Projected future savings minus current principal"
    )

    st.markdown("**Principal Debt Breakdown:**")
    pd1, pd2, pd3 = st.columns(3)
    pd1.metric("Current Principal Debt",      fmt(principal_left))
    pd2.metric("Principal After 1 Year",      fmt(principal_after_1yr))
    pd3.metric(
        "Principal Reduced in 1 Year",
        fmt(principal_left - principal_after_1yr),
        delta=f"-{fmt(principal_left - principal_after_1yr)}",
        delta_color="inverse"
    )

    nw_df = pd.DataFrame({
        "Period":    ["Today", "1 Year", f"{years} Years"],
        "Net Worth": [current_networth, savings - principal_after_1yr, future_networth]
    })
    fig_nw = px.bar(
        nw_df, x="Period", y="Net Worth",
        color="Net Worth",
        color_continuous_scale="Blues",
        title="Net Worth Over Time"
    )
    fig_nw.update_layout(
        plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
        font_color="white", height=300
    )
    st.plotly_chart(fig_nw, use_container_width=True)

    st.divider()

    # ----------------------------------------------------------
    # SECTION 4 — LOAN CLOSING STRATEGY
    # ----------------------------------------------------------
    section("", "Loan Closing Strategy")

    if not df_loans.empty and total_income > 0:
        df_strat    = df_loans[df_loans["emi"] > 0].copy()
        df_strat    = df_strat.sort_values("emi", ascending=False).reset_index(drop=True)
        emi_limit   = total_income * 0.40
        running_emi = 0
        close_list  = []
        safe_list   = []

        for _, row in df_strat.iterrows():
            running_emi += row["emi"]
            if running_emi > emi_limit:
                close_list.append(row)
            else:
                safe_list.append(row)

        s1, s2 = st.columns(2)
        s1.metric("Safe EMI Limit (40% of Income)", fmt(emi_limit))
        over_under = "over" if total_emi > emi_limit else "under"
        s2.metric(
            "Your Current Total EMI",
            fmt(total_emi),
            delta=f"{fmt(abs(total_emi - emi_limit))} {over_under} limit",
            delta_color="inverse"
        )

        if close_list:
            st.error(
                f"{len(close_list)} loan(s) are pushing you beyond the 40% EMI safety limit. "
                f"Close these first:"
            )
            for row in close_list:
                mo_close     = round(row["principal"] / row["emi"]) if row["emi"] > 0 else 0
                stress_pct   = round((row["emi"] / max(total_emi, 1)) * 100, 1)
                extra_per_mo = max(0, row["emi"] - (emi_limit / max(len(df_strat), 1)))
                st.markdown(f"""
<div class="loan-card">
  <b>{row['name']}</b><br>
  EMI: {fmt(row['emi'])} &nbsp;|&nbsp;
  Principal Left: {fmt(row['principal'])} &nbsp;|&nbsp;
  Close in: ~{mo_close} months &nbsp;|&nbsp;
  Extra needed: {fmt(extra_per_mo)}/month &nbsp;|&nbsp;
  Stress reduction if closed: <b>{stress_pct}%</b>
</div>""", unsafe_allow_html=True)
        else:
            st.success("All loans are within the 40% EMI safety limit.")

        if safe_list:
            st.info(f"{len(safe_list)} loan(s) are within the safe EMI range:")
            for row in safe_list:
                st.markdown(f"""
<div class="loan-card">
  <b>{row['name']}</b> — EMI: {fmt(row['emi'])} (Safe — continue paying)
</div>""", unsafe_allow_html=True)

        monthly_extra_req = max(0, total_emi - emi_limit)
        if monthly_extra_req > 0:
            st.warning(
                f"You need {fmt(monthly_extra_req)} extra income per month "
                f"OR close high-EMI loans to reach the safe 40% zone."
            )
    else:
        st.info("Add loan and income data for strategy analysis.")

    st.divider()

    # ----------------------------------------------------------
    # SECTION — LOAN CLOSURE PREDICTION (REDESIGNED)
    # ----------------------------------------------------------
    section("", "Loan Closure Prediction")

    st.markdown(
        "This section uses the loans you already entered above. "
        "Select your prediction period and instantly see closure timelines, "
        "principal progress, balance impact, and smart suggestions."
    )

    # Use loans from the main Loan Information section (df_loans)
    valid_pred_loans = [
        {
            "name":       row["name"] or f"Loan {i+1}",
            "emi":        row["emi"],
            "principal":  row["principal"],
            "months_rem": row["months"],
        }
        for i, row in df_loans.iterrows()
        if row["emi"] > 0 and row["principal"] > 0
    ]

    pred_years_sel    = st.selectbox("Prediction Period", [1, 2, 3, 5], index=0, key="pred_years_sel")
    pred_months_total = pred_years_sel * 12

    if valid_pred_loans:

        # ── Per-loan closure summary ──
        st.markdown(f"**📋 Loan Closure Summary — {pred_years_sel} Year View:**")

        pred_summary_rows = []
        for loan in valid_pred_loans:
            m_to_close = int(loan["months_rem"]) if loan["months_rem"] > 0 \
                         else int(loan["principal"] / loan["emi"])
            closes_within = m_to_close <= pred_months_total
            if closes_within:
                status = f"✅ Closes at Month {m_to_close}"
            else:
                beyond = m_to_close - pred_months_total
                status = f"⚠️ {beyond} months beyond {pred_years_sel}yr"

            # Principal remaining after pred_months_total
            months_paid_so_far = min(m_to_close, pred_months_total)
            principal_remaining = max(loan["principal"] - loan["emi"] * months_paid_so_far, 0)
            principal_cleared   = loan["principal"] - principal_remaining
            pct_cleared         = round((principal_cleared / max(loan["principal"], 1)) * 100, 1)

            pred_summary_rows.append({
                "Loan":                    loan["name"],
                "Monthly EMI":             fmt(loan["emi"]),
                "Starting Principal":      fmt(loan["principal"]),
                "Months to Close":         m_to_close,
                "Principal Cleared":       fmt(principal_cleared),
                "Principal Remaining":     fmt(principal_remaining),
                "% Cleared":               f"{pct_cleared}%",
                "Status":                  status,
            })

        df_pred_table = pd.DataFrame(pred_summary_rows)
        st.dataframe(df_pred_table, use_container_width=True)

        # ── Principal Progress bar per loan ──
        st.markdown("** Principal Clearance Progress per Loan:**")
        for row in pred_summary_rows:
            pct_val = float(row["% Cleared"].replace("%", ""))
            colour  = "normal" if pct_val >= 100 else ("normal" if pct_val > 50 else "off")
            st.markdown(f"**{row['Loan']}** — Cleared: {row['Principal Cleared']}  |  Remaining: {row['Principal Remaining']}  ({row['% Cleared']})")
            st.progress(min(int(pct_val), 100))

        # ── Month-by-month 12-month rolling prediction ──
        st.markdown("** Month-by-Month 1-Year Prediction (Balance with Loan Closures):**")

        running_loans_pred = []
        for loan in valid_pred_loans:
            m_rem = int(loan["months_rem"]) if loan["months_rem"] > 0 \
                    else int(loan["principal"] / loan["emi"])
            running_loans_pred.append({
                "name":       loan["name"],
                "emi":        loan["emi"],
                "bal":        float(loan["principal"]),
                "months_rem": m_rem,
                "closed":     False,
                "closed_at":  None,
            })

        cum_balance_pred  = float(savings)
        monthly_pred_rows = []

        for m in range(1, 13):
            active_emi_pred = sum(l["emi"] for l in running_loans_pred if not l["closed"])
            net_this_month  = total_income - active_emi_pred
            cum_balance_pred += net_this_month

            closed_names_this = []
            for l in running_loans_pred:
                if not l["closed"]:
                    l["bal"]        -= l["emi"]
                    l["months_rem"] -= 1
                    if l["bal"] <= 0 or l["months_rem"] <= 0:
                        l["closed"]    = True
                        l["closed_at"] = m
                        closed_names_this.append(l["name"])

            monthly_pred_rows.append({
                "Month":            m,
                "Active EMI":       fmt(active_emi_pred),
                "Net This Month":   fmt(net_this_month),
                "Cumulative Balance": round(cum_balance_pred, 0),
                "Loan(s) Closed":   ", ".join(closed_names_this) if closed_names_this else "—",
            })

        df_monthly_pred = pd.DataFrame(monthly_pred_rows)

        # display with formatted balance
        df_display = df_monthly_pred.copy()
        df_display["Cumulative Balance"] = df_display["Cumulative Balance"].apply(fmt)
        st.dataframe(df_display, use_container_width=True)

        # ── Balance area chart ──
        df_chart_pred = pd.DataFrame({
            "Month":   [r["Month"] for r in monthly_pred_rows],
            "Balance": [r["Cumulative Balance"] for r in monthly_pred_rows],
        })
        fig_pred_bal = px.area(
            df_chart_pred, x="Month", y="Balance",
            color_discrete_sequence=["#38bdf8"],
            title="Predicted Balance Over 12 Months (Loan Closures Factored In)"
        )
        fig_pred_bal.update_layout(
            plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
            font_color="white", height=320
        )
        st.plotly_chart(fig_pred_bal, use_container_width=True)

        # ── 1-Year Summary KPIs ──
        final_balance_pred = df_chart_pred["Balance"].iloc[-1]
        loans_closed_pred  = [l for l in running_loans_pred if l["closed"]]
        loans_open_pred    = [l for l in running_loans_pred if not l["closed"]]
        freed_emi_pred     = sum(l["emi"] for l in loans_closed_pred)

        sk1, sk2, sk3, sk4 = st.columns(4)
        sk1.metric("Balance After 1 Year",              fmt(final_balance_pred))
        sk2.metric("Loans Closed Within 1 Year",        str(len(loans_closed_pred)))
        sk3.metric("Loans Still Active After 1 Year",   str(len(loans_open_pred)))
        sk4.metric("Monthly EMI Freed After Closures",  fmt(freed_emi_pred))

        # ── Multi-year balance impact with loan-closure waterfall ──
        st.markdown(f"**📈 {pred_years_sel}-Year Balance Projection (Dynamic — Closures Applied):**")

        # Re-run full multi-year simulation
        ml2 = []
        for loan in valid_pred_loans:
            m_rem = int(loan["months_rem"]) if loan["months_rem"] > 0 \
                    else int(loan["principal"] / loan["emi"])
            ml2.append({
                "name": loan["name"], "emi": loan["emi"],
                "bal": float(loan["principal"]),
                "months_rem": m_rem, "closed": False
            })

        cum2       = float(savings)
        proj_rows  = []
        for m in range(1, pred_months_total + 1):
            act_emi = sum(l["emi"] for l in ml2 if not l["closed"])
            cum2   += (total_income - act_emi)
            for l in ml2:
                if not l["closed"]:
                    l["bal"]        -= l["emi"]
                    l["months_rem"] -= 1
                    if l["bal"] <= 0 or l["months_rem"] <= 0:
                        l["closed"] = True
            proj_rows.append({"Month": m, "Balance": round(cum2, 0)})

        df_proj2   = pd.DataFrame(proj_rows)
        start_bal  = float(savings)
        end_bal    = df_proj2["Balance"].iloc[-1]
        delta_bal  = end_bal - start_bal

        fig_proj2 = px.area(
            df_proj2, x="Month", y="Balance",
            color_discrete_sequence=["#22c55e" if delta_bal >= 0 else "#ef4444"],
            title=f"{pred_years_sel}-Year Balance Projection with Actual Loan Closure Events"
        )
        fig_proj2.update_layout(
            plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
            font_color="white", height=340
        )
        st.plotly_chart(fig_proj2, use_container_width=True)

        # ── GAIN / LOSS ALERT ──
        gain_label = "📈 BALANCE GAIN" if delta_bal >= 0 else "📉 BALANCE LOSS"
        card_class  = "alert-gain"      if delta_bal >= 0 else "alert-loss"
        st.markdown(f"""
<div class="{card_class}">
  <b>{gain_label} over {pred_years_sel} Year(s)</b><br>
  Starting Balance: {fmt(start_bal)} &nbsp;→&nbsp;
  Ending Balance: {fmt(end_bal)}<br>
  Change: <b>{fmt(delta_bal)}</b>
  {"&nbsp; ✅ Your loans closing early free up cash, boosting your balance!" if delta_bal >= 0
   else "&nbsp; ⚠️ EMI burden exceeds income. Close high-EMI loans to reverse this."}
</div>""", unsafe_allow_html=True)

        # ── HOW LONG TO CLOSE TOTAL PRINCIPAL in 1 year ──
        st.markdown("** Principal Closure Timeline & Suggestions:**")

        total_principal_all  = sum(l["principal"] for l in valid_pred_loans)
        total_emi_all        = sum(l["emi"] for l in valid_pred_loans)
        months_to_clear_all  = int(total_principal_all / total_emi_all) if total_emi_all > 0 else 999

        pc1, pc2 = st.columns(2)
        pc1.metric("Total Principal (All Loans)", fmt(total_principal_all))
        pc2.metric(
            "Estimated Months to Clear All Principal",
            f"{months_to_clear_all} months ({months_to_clear_all/12:.1f} yrs)"
        )

        # Suggestion: how much extra to close all within 1 year
        if months_to_clear_all > 12:
            # Extra needed per month so principal clears in 12 months
            extra_to_close_1yr = max(0, int(total_principal_all / 12) - total_emi_all)
            st.markdown(f"""
<div class="info-card">
  💡 <b>Suggestion:</b> To close <b>all principal within 1 year</b>, you need to pay
  an extra <b>{fmt(extra_to_close_1yr)}/month</b> on top of your current EMI of {fmt(total_emi_all)}.
  <br>Total monthly payment required: <b>{fmt(total_emi_all + extra_to_close_1yr)}</b>
</div>""", unsafe_allow_html=True)
        else:
            st.success(f"✅ At current EMI rate, all principal clears within {months_to_clear_all} months — well within 1 year!")

        # Per-loan suggestion
        st.markdown("**Per-Loan Closure Suggestions:**")
        for loan in valid_pred_loans:
            m_rem = int(loan["months_rem"]) if loan["months_rem"] > 0 \
                    else int(loan["principal"] / loan["emi"])
            if m_rem > 12:
                extra_needed_1yr = max(0, int(loan["principal"] / 12) - loan["emi"])
                st.markdown(f"""
<div class="info-card">
   <b>{loan['name']}</b>: Closes in {m_rem} months. 
  Pay extra <b>{fmt(extra_needed_1yr)}/month</b> to close within 1 year.
  (Current EMI: {fmt(loan['emi'])} → Required: {fmt(loan['emi'] + extra_needed_1yr)}/month)
</div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
<div class="alert-gain">
  ✅ <b>{loan['name']}</b>: Closes in {m_rem} months — within 1 year at current EMI. No extra payment needed.
</div>""", unsafe_allow_html=True)

        # ── Loan closure events summary ──
        if loans_closed_pred:
            st.success(
                f"Loans closing within 1 year: "
                f"{', '.join(l['name'] for l in loans_closed_pred)} — "
                f"EMI freed: {fmt(freed_emi_pred)}/month after closure"
            )
        if loans_open_pred:
            st.info(
                f"Loans still active after 1 year: "
                f"{', '.join(l['name'] for l in loans_open_pred)}"
            )

    else:
        st.info(
            "Add loans in the **Loan Information** section above (EMI + Principal required) "
            "to see closure predictions here."
        )

    st.divider()

    # ----------------------------------------------------------
    # SECTION 5 — EXTRA INCOME SUGGESTIONS
    # ----------------------------------------------------------
    section("", "Extra Income Suggestions")

    family_expenses     = total_income * 0.40
    personal_lifestyle  = total_income * 0.15
    required_total      = total_emi + family_expenses + personal_lifestyle
    extra_income_needed = max(0, required_total - total_income)

    st.markdown("**Monthly Obligation Breakdown:**")
    e1, e2, e3, e4 = st.columns(4)
    e1.metric("EMI Total",       fmt(total_emi))
    e2.metric("Family (40%)",    fmt(family_expenses))
    e3.metric("Lifestyle (15%)", fmt(personal_lifestyle))
    e4.metric("Total Required",  fmt(required_total))

    if extra_income_needed > 0:
        st.error(f"You need {fmt(extra_income_needed)} extra per month to cover all obligations.")
        allocations = [
            ("Freelancing / Consulting",            0.40),
            ("Online Business (Flipkart / Amazon)",  0.20),
            ("Teaching / Online Courses",            0.15),
            ("Investments (Index Funds / Stocks)",   0.15),
            ("Content Creation / YouTube",           0.10),
        ]
        st.markdown("**Income Target Allocation Plan:**")
        for label, share in allocations:
            target = round(extra_income_needed * share)
            st.markdown(
                f'<div class="info-card">'
                f'<b>{label}</b> — Target: {fmt(target)}/month ({int(share*100)}% of extra needed)'
                f'</div>',
                unsafe_allow_html=True
            )
    else:
        surplus = total_income - required_total
        st.success(f"Income covers all obligations. Monthly surplus: {fmt(surplus)}")
        st.write(f"Total obligations: {fmt(required_total)}  |  Your income: {fmt(total_income)}")

    st.divider()

    # ----------------------------------------------------------
    # STRESS SOURCE DETECTION
    # ----------------------------------------------------------
    section("", "Stress Source Detection")

    if not df_loans.empty:
        stress_df = df_loans[df_loans["emi"] > 0].sort_values("emi", ascending=False)
        if not stress_df.empty:
            top = stress_df.iloc[0]
            pct = round((top["emi"] / max(total_emi, 1)) * 100, 1)
            st.error(
                f"Highest stress loan: {top['name']} — "
                f"EMI {fmt(top['emi'])} ({pct}% of total EMI)"
            )
            fig_pie = px.pie(
                df_loans[df_loans["emi"] > 0],
                values="emi", names="name",
                title="EMI Distribution Across Loans",
                color_discrete_sequence=px.colors.sequential.Blues_r
            )
            fig_pie.update_layout(
                paper_bgcolor="#0f172a", font_color="white", height=320
            )
            st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No loan data to detect stress source.")

    st.divider()

    # ----------------------------------------------------------
    # AI FINANCIAL ADVISOR
    # ----------------------------------------------------------
    section("", "AI Financial Advisor")

    q = st.text_input(
        "Ask a finance question:",
        placeholder="e.g. How can I reduce my loan burden?"
    )
    if q:
        ql = q.lower()
        if any(w in ql for w in ["loan", "emi", "debt", "close", "pay"]):
            st.write(
                "Focus on clearing the highest-EMI loan first to reduce financial stress fastest. "
                "Even an extra Rs. 1,000–2,000 per month toward the principal accelerates payoff."
            )
        elif any(w in ql for w in ["save", "saving", "savings", "emergency"]):
            st.write(
                "Build an emergency fund of 6 months of expenses before aggressive investing. "
                "Keep it in a liquid fund or high-interest savings account."
            )
        elif any(w in ql for w in ["invest", "investment", "stock", "mutual", "fund"]):
            st.write(
                "Start with index funds (Nifty 50 / Sensex) for stable long-term growth. "
                "Invest at least 10–15% of income monthly via SIP once EMI is under control."
            )
        elif any(w in ql for w in ["income", "earn", "salary", "extra"]):
            st.write(
                "Focus on one high-return side income stream first. Freelancing or consulting "
                "in your primary skill is the fastest way to add Rs. 5,000–20,000 per month."
            )
        elif any(w in ql for w in ["budget", "plan", "manage", "spend"]):
            st.write(
                "Follow the 50/30/20 rule: 50% for needs (EMI + family), "
                "30% for wants, 20% for savings and investments. "
                "Automate EMI payments to avoid penalties."
            )
        else:
            st.write(
                "General rule: Keep total EMI below 40% of income. "
                "Maintain 6 months emergency fund. "
                "Invest 15% or more in diversified instruments once debt is managed."
            )

    st.divider()

    # ----------------------------------------------------------
    # SECTION 6 — ANALYSIS HISTORY & DELETE
    # ----------------------------------------------------------
    section("️", "Analysis History")

    history = load_history()

    if st.button("Save Current Analysis to History"):
        entry = {
            "id":             str(int(time.time())),
            "date":           datetime.now().strftime("%d %b %Y, %H:%M"),
            "income":         total_income,
            "total_emi":      total_emi,
            "balance":        balance,
            "principal_left": principal_left,
            "loan_count":     loan_count,
            "risk_score":     risk_score,
            "loans":          loan_data
        }
        history.append(entry)
        save_history(history)
        st.success("Analysis saved successfully!")
        st.rerun()

    if history:
        st.markdown(f"**{len(history)} saved record(s):**")
        for entry in reversed(history):
            label = (
                f"{entry['date']}  |  "
                f"Income: {fmt(entry['income'])}  |  "
                f"EMI: {fmt(entry['total_emi'])}  |  "
                f"Risk: {entry['risk_score']}%"
            )
            with st.expander(label):
                h1, h2, h3, h4 = st.columns(4)
                h1.metric("Income",     fmt(entry['income']))
                h2.metric("Total EMI",  fmt(entry['total_emi']))
                h3.metric("Balance",    fmt(entry['balance']))
                h4.metric("Risk Score", f"{entry['risk_score']}%")
                st.write(
                    f"Loans: {entry['loan_count']}  |  "
                    f"Principal Left: {fmt(entry['principal_left'])}"
                )
                if st.button("Delete this record", key=f"del_{entry['id']}"):
                    history = [h for h in history if h["id"] != entry["id"]]
                    save_history(history)
                    st.warning("Record deleted.")
                    st.rerun()
    else:
        st.info("No saved analyses yet. Click 'Save Current Analysis' above after analyzing.")

    st.divider()

    # ----------------------------------------------------------
    # SECTION 7 — QUICK CALCULATOR
    # ----------------------------------------------------------
    section("", "Quick Calculator")

    tab_emi, tab_savings, tab_invest = st.tabs([
        "EMI Calculator",
        "Savings Goal",
        "Investment Return (SIP)"
    ])

    with tab_emi:
        st.markdown("**Calculate EMI for any loan instantly**")
        t1c1, t1c2, t1c3 = st.columns(3)
        q_principal = t1c1.number_input("Loan Amount (Rs.)",         min_value=0,   value=500000, step=10000, key="qc_p")
        q_rate      = t1c2.number_input("Annual Interest Rate (%)",  min_value=0.0, value=10.0,   step=0.1,   key="qc_r")
        q_tenure    = t1c3.number_input("Tenure (Months)",           min_value=1,   value=60,                key="qc_t")
        if q_principal > 0 and q_rate > 0 and q_tenure > 0:
            r         = q_rate / (12 * 100)
            emi_calc  = q_principal * r * (1 + r)**q_tenure / ((1 + r)**q_tenure - 1)
            total_pay = emi_calc * q_tenure
            total_int = total_pay - q_principal
            rc1, rc2, rc3 = st.columns(3)
            rc1.metric("Monthly EMI",    fmt(emi_calc))
            rc2.metric("Total Interest", fmt(total_int))
            rc3.metric("Total Payment",  fmt(total_pay))
            fig_ep = px.pie(
                values=[q_principal, total_int],
                names=["Principal", "Interest"],
                color_discrete_sequence=["#38bdf8", "#ef4444"],
                title="Principal vs Interest Split"
            )
            fig_ep.update_layout(paper_bgcolor="#0f172a", font_color="white", height=280)
            st.plotly_chart(fig_ep, use_container_width=True)

    with tab_savings:
        st.markdown("**How long to reach your savings target?**")
        sg1, sg2 = st.columns(2)
        goal_amount  = sg1.number_input("Target Savings (Rs.)",  min_value=0, value=1000000, step=50000, key="sg_g")
        monthly_save = sg2.number_input("Monthly Saving (Rs.)",  min_value=0, value=10000,   step=1000,  key="sg_m")
        if monthly_save > 0 and goal_amount > 0:
            months_to_goal = goal_amount / monthly_save
            st.metric(
                "Time to Reach Goal",
                f"{months_to_goal:.0f} months  ({months_to_goal/12:.1f} years)"
            )
            progress_pct = min(int((savings / goal_amount) * 100), 100)
            st.write(f"Current savings: {fmt(savings)} — {progress_pct}% of goal reached")
            st.progress(progress_pct)

    with tab_invest:
        st.markdown("**SIP compound return calculator**")
        ir1, ir2, ir3 = st.columns(3)
        inv_amount = ir1.number_input("Monthly Investment (Rs.)",    min_value=0,   value=5000,  step=500,  key="ir_a")
        inv_rate   = ir2.number_input("Expected Annual Return (%)",  min_value=0.0, value=12.0,  step=0.5,  key="ir_r")
        inv_years  = ir3.number_input("Investment Period (Years)",   min_value=1,   value=10,              key="ir_y")
        if inv_amount > 0 and inv_rate > 0:
            r_m      = inv_rate / (12 * 100)
            n_m      = inv_years * 12
            fv       = inv_amount * ((1 + r_m)**n_m - 1) / r_m * (1 + r_m)
            invested = inv_amount * n_m
            ret      = fv - invested
            i1, i2, i3 = st.columns(3)
            i1.metric("Total Invested",    fmt(invested))
            i2.metric("Estimated Returns", fmt(ret))
            i3.metric("Future Value",      fmt(fv))
            sip_rows = []
            cum = 0.0; inv_cum = 0.0
            for m in range(1, n_m + 1):
                cum     = cum * (1 + r_m) + inv_amount
                inv_cum += inv_amount
                sip_rows.append({"Month": m, "Portfolio Value": cum, "Amount Invested": inv_cum})
            df_sip = pd.DataFrame(sip_rows)
            fig_sip = px.line(
                df_sip, x="Month", y=["Portfolio Value", "Amount Invested"],
                title=f"SIP Growth over {inv_years} Year(s)",
                color_discrete_map={"Portfolio Value": "#38bdf8", "Amount Invested": "#94a3b8"}
            )
            fig_sip.update_layout(
                plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                font_color="white", height=320
            )
            st.plotly_chart(fig_sip, use_container_width=True)

    st.divider()

    # ----------------------------------------------------------
    # PDF REPORT DOWNLOAD
    # ----------------------------------------------------------
    section("", "Download Report")

    if st.button("Generate PDF Report"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "AI Personal Wealth Analyzer - Report", ln=True, align="C")
        pdf.set_font("Arial", "", 12)
        pdf.ln(5)
        pdf.cell(0, 8, f"Date: {datetime.now().strftime('%d %b %Y, %H:%M')}", ln=True)
        pdf.ln(3)
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 8, "Income & Balance", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 7, f"  Monthly Income   : {fmt(total_income)}",  ln=True)
        pdf.cell(0, 7, f"  Total EMI        : {fmt(total_emi)}",     ln=True)
        pdf.cell(0, 7, f"  Monthly Balance  : {fmt(balance)}",       ln=True)
        pdf.cell(0, 7, f"  Savings          : {fmt(savings)}",       ln=True)
        pdf.ln(3)
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 8, "Loan Summary", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 7, f"  Number of Loans  : {loan_count}",                         ln=True)
        pdf.cell(0, 7, f"  Total Principal  : {fmt(principal_left)}",                ln=True)
        pdf.ln(3)
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 8, "Risk & Net Worth", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 7, f"  Debt Risk Score  : {risk_score}%",                        ln=True)
        pdf.cell(0, 7, f"  Current Net Worth: {fmt(savings - principal_left)}",      ln=True)
        net_1yr = savings - max(principal_left - total_emi * 12, 0)
        pdf.cell(0, 7, f"  Net Worth 1 Year : {fmt(net_1yr)}",                       ln=True)
        pdf.output("finance_report.pdf")
        with open("finance_report.pdf", "rb") as f:
            st.download_button("Download PDF", f, "finance_report.pdf", mime="application/pdf")

    st.markdown("""
<div style='text-align:center; padding:25px; color:#94a3b8; font-size:14px;'>
    Author by Sai vignesh &nbsp;|&nbsp; AI Personal Wealth Analyzer &nbsp;|&nbsp;
    <i>Results are for guidance only, not professional financial advice.</i>
</div>
""", unsafe_allow_html=True)
