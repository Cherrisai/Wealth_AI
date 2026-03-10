# 💰 AI Personal Wealth Analyzer

An AI-powered personal finance dashboard built with Streamlit. Enter your income, loans, and savings to get a complete financial health analysis — stress predictions, debt risk scoring, net worth projections, and actionable advice.

---

## Features

- **AI Financial Stress Prediction** — ML model classifies stress level as Low / Moderate / High
- **Debt Risk Gauge** — EMI-to-income ratio visualized on a live gauge chart
- **Future Balance Projection** — Configurable multi-year savings forecast
- **Additional Payment Simulator** — See how extra EMI payments accelerate loan closure
- **Net Worth Analysis** — Current, 1-year, and multi-year net worth breakdown
- **Loan Closing Strategy** — Prioritized loan closure recommendations (40% EMI safety rule)
- **Loan Closure Prediction** — Month-by-month closure timeline with principal progress bars
- **Extra Income Suggestions** — Allocation plan if income falls short of obligations
- **Stress Source Detection** — EMI distribution pie chart highlighting the highest-stress loan
- **AI Financial Advisor** — Keyword-based Q&A for finance guidance
- **Quick Calculator** — EMI calculator, savings goal tracker, and SIP return estimator
- **Analysis History** — Save, browse, and delete past analyses (stored in JSON)
- **PDF Report Download** — One-click downloadable financial summary report

---

## Project Structure

```
├── app.py                  # Main Streamlit application
├── finance_model.pkl       # Pre-trained ML model (required)
├── requirements.txt        # Python dependencies
├── analysis_history.json   # Auto-created on first save (do not delete manually)
└── finance_report.pdf      # Auto-created on PDF export
```

---

## Prerequisites

- Python 3.9 or higher
- `finance_model.pkl` — a trained scikit-learn classifier in the same directory as `app.py`

### Model Input Features (in order)

The model expects a single row with these 7 features:

| # | Feature | Description |
|---|---------|-------------|
| 1 | `income` | Monthly salary (Rs.) |
| 2 | `extra_income` | Additional monthly income (Rs.) |
| 3 | `loan_count` | Number of active loans |
| 4 | `total_emi` | Sum of all monthly EMIs (Rs.) |
| 5 | `principal_left` | Total outstanding principal (Rs.) |
| 6 | `months_left` | Maximum months remaining across all loans |
| 7 | `savings` | Current savings balance (Rs.) |

### Model Output Classes

| Value | Meaning |
|-------|---------|
| `0` | Low Financial Stress |
| `1` | Moderate Financial Stress |
| `2` | High Financial Stress |

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/ai-wealth-analyzer.git
cd ai-wealth-analyzer

# 2. (Recommended) Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Place your trained model in the project root
cp /path/to/finance_model.pkl .

# 5. Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501` in your browser.

---

## Usage

1. **Enter Income** — Monthly salary, any extra income, and current savings
2. **Add Loans** — Click "Add Loan" for each active loan and fill in EMI, principal, and months remaining
3. **Click "Analyze My Financial Health"** — All sections populate instantly
4. **Explore sections** — Adjust sliders for projection years, extra payments, and simulation periods
5. **Save or Export** — Save to history or download a PDF report

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `streamlit` | Web app framework |
| `numpy` | Numerical computations |
| `pandas` | Data manipulation |
| `scikit-learn` | Loading the `.pkl` ML model |
| `plotly` | Interactive charts and gauge |
| `fpdf2` | PDF report generation |

---

## Notes

- All financial figures are displayed in Indian number format (K / L / Cr)
- Analysis history is persisted locally in `analysis_history.json`
- Results are for **guidance only** and do not constitute professional financial advice

---

*Author: Sai Vignesh*