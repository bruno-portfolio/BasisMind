import streamlit as st

st.set_page_config(page_title="Documentation | BasisMind", page_icon="📚", layout="wide")

st.title("📚 Technical Documentation")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Overview", "Components", "Overrides", "Architecture", "API"]
)

with tab1:
    st.markdown(
        """
    ## Overview

    The **Decision Engine** is a decision support system for physical grain (soybean)
    trading operations, designed to:

    - **Standardize** market reading
    - **Reduce** subjective bias in decisions
    - **Transform** scattered signals into consistent recommendations
    - **Ensure** traceability and auditability

    ### What the Engine does NOT do

    - Does not predict future prices
    - Does not replace human judgment
    - Does not capture geopolitical events
    - Does not guarantee results

    ---

    ## Questions the Engine Answers

    | Axis | Question | Possible Answers |
    |------|----------|------------------|
    | **Physical** | What is the recommendation for physical position? | Increase, Hold, Reduce |
    | **Hedge** | What is the recommendation for Chicago hedge? | Increase, Hold, Reduce |

    Each recommendation includes:
    - **Intensity**: Strong, Moderate, or Neutral
    - **Sizing**: Suggested position percentage
    - **Justification**: Explanation of signals that drove the decision

    ---

    ## Decision Flow

    ```
    1. MARKET INPUTS
       │
       ├── Premium (percentile by regime)
       ├── Line-up (weekly variation)
       ├── Competitiveness (adjusted FOB spread)
       ├── Demand (pace z-score)
       ├── FX Rate (5d variation)
       └── Chicago (percentile + spike)
       │
       ▼
    2. SCORING ENGINE
       │
       ├── Normalize each component to [0-100]
       ├── Weight by calibrated weights
       └── Final aggregate score [0-100]
       │
       ▼
    3. OVERRIDE RULES
       │
       ├── Check 5 override conditions
       ├── If active: replace recommendation
       └── Hierarchy: most conservative prevails
       │
       ▼
    4. BOOK MODULATION
       │
       ├── Check exposure limits
       ├── Check hedge target
       └── Adjust sizing if necessary
       │
       ▼
    5. OUTPUT
       │
       ├── Physical Recommendation + Sizing
       ├── Hedge Recommendation + Delta
       └── Traceable justification
    ```
    """
    )


with tab2:
    st.markdown(
        """
    ## Score Components

    The physical score is calculated as a weighted average of 5 components:

    ### Line-up (30%)

    **What it measures:** Real demand, based on ships scheduled for loading.

    **Input:** Weekly percentage variation of net line-up

    **Transformation:**
    ```
    score = linear_map(weekly_var, -15%, +15%, 0, 100)
    ```

    | Variation | Score | Interpretation |
    |-----------|-------|----------------|
    | < -15% | 0 | Strong drop |
    | -15% to +15% | 0-100 | Linear |
    | > +15% | 100 | Strong rise |

    ---

    ### Premium (25%)

    **What it measures:** Price level relative to same regime history.

    **Input:** Current premium percentile vs last 3 years of same regime (crop or off-season)

    **Regimes:**
    - **Crop Season:** March to July
    - **Off-Season:** August to February

    **Why percentile and not z-score?**
    - Premiums have asymmetric distribution (fat tails)
    - Percentile is more robust to outliers
    - Does not assume normality

    ---

    ### Competitiveness (20%)

    **What it measures:** Brazil expensive or cheap vs competing origins.

    **Input:** Adjusted FOB spread = (FOB Paranagua - FOB US Gulf) + freight adjustment

    **Freight Adjustment (monthly lookup):**
    | Month | Adjustment | Month | Adjustment |
    |-------|------------|-------|------------|
    | Jan | -8 | Jul | +2 |
    | Feb | -10 | Aug | +5 |
    | Mar | -12 | Sep | +8 |
    | Apr | -10 | Oct | +10 |
    | May | -6 | Nov | +6 |
    | Jun | -2 | Dec | 0 |

    **Transformation (inverse):**
    ```
    score = linear_map(spread, +20, -20, 0, 100)
    ```
    - Negative spread (Brazil cheap) = High score
    - Positive spread (Brazil expensive) = Low score

    ---

    ### Demand (15%)

    **What it measures:** Export pace vs historical average.

    **Input:** Z-score = (weekly_exports - 5y_avg) / 5y_std

    **Transformation:**
    ```
    score = linear_map(z_pace, -1.5, +1.5, 0, 100)
    ```

    | Z-Score | Score | Interpretation |
    |---------|-------|----------------|
    | < -1.5 | 0 | Very weak demand |
    | -1.5 to +1.5 | 0-100 | Linear |
    | > +1.5 | 100 | Very strong demand |

    ---

    ### FX Rate (10%)

    **What it measures:** Margin modulator (strong real = better USD margin).

    **Input:** USD/BRL variation in 5 days

    **Transformation (inverse):**
    ```
    score = linear_map(var_5d, +3%, -3%, 0, 100)
    ```
    - Strong real (negative variation) = High score
    - Weak real (positive variation) = Low score
    """
    )


with tab3:
    st.markdown(
        """
    ## Override Rules

    Overrides are conditions that **dominate** scoring, representing market situations
    that rarely fail and require specific action.

    ### Priority Hierarchy

    | Priority | Override | Description |
    |----------|----------|-------------|
    | 1 (highest) | **Logistics** | Significant logistics risk |
    | 2 | **Joint Drop** | Market exiting |
    | 3 | **Premium Trap** | Price will correct |
    | 4 | **Critical Competitiveness** | Brazil non-competitive |
    | 5 | **Speculative Chicago** | Spike without fundamentals |

    When multiple overrides are active, the one with **highest priority** is applied.

    ---

    ### 1. Logistics Override

    **Condition:**
    ```
    LOGISTICS_FLAG = TRUE
    ```

    **Triggers:**
    - Wait time > 15 days for 2+ consecutive weeks
    - Loading rate < 70% of capacity
    - Manual event (strike, interdiction)

    **Action:** STRONG REDUCE (-30%)

    **Rationale:** Logistics bottleneck will be priced before the event.

    ---

    ### 2. Joint Drop Override

    **Condition:**
    ```
    lineup_var < -10%  AND  premium_percentile < 40
    ```

    **Interpretation:** Real demand is exiting. It's not "cheap", it's market exiting.

    **Action:** REDUCE (-20%)

    ---

    ### 3. Premium Trap Override

    **Condition:**
    ```
    premium_percentile > 80  AND  lineup_var < -10%
    ```

    **Interpretation:** Price hasn't corrected yet, but demand is already leaving.

    **Action:** STRONG REDUCE (-25%)

    **Rationale:** Capture premium via accelerated sales before correction.

    ---

    ### 4. Critical Competitiveness Override

    **Condition:**
    ```
    adjusted_spread > +15 USD/ton
    ```

    **Interpretation:** Buyer has cheaper alternative (US Gulf).

    **Action:** REDUCE (-15%)

    ---

    ### 5. Speculative Chicago Override

    **Condition:**
    ```
    chicago_spike = TRUE  AND  confirmed_narrative = FALSE
    ```

    **Spike definition:** Chicago rose > 5% in 5 days

    **Interpretation:** Speculative move with negative asymmetry.

    **Action:** HOLD physical + STRONG INCREASE HEDGE (+20pp)
    """
    )


with tab4:
    st.markdown(
        """
    ## System Architecture

    ### Module Structure

    ```
    src/
    ├── config.py          # Constants and thresholds
    ├── database.py        # SQLite schema, CRUD
    ├── validators.py      # Data validation
    ├── pipeline.py        # Data ingestion
    ├── alerts.py          # Alert system
    ├── premium.py         # Block 2: Premium normalization
    ├── lineup.py          # Block 3: Line-up indicators
    ├── competitiveness.py # Block 4: Competitiveness
    ├── auxiliaries.py     # Block 5: FX, demand, logistics
    ├── scoring.py         # Block 6: Scoring engine
    ├── overrides.py       # Block 7: Override rules
    ├── book.py            # Block 8: Book state
    ├── engine.py          # Block 8: Integrated engine
    └── __init__.py        # Exports
    ```

    ### Data Flow

    ```
    ┌──────────────────┐
    │   Market Data    │
    │  (Raw Inputs)    │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │    Validators    │
    │  (Data Quality)  │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │   Normalizers    │
    │ (Premium, etc.)  │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Scoring Engine  │
    │  (Aggregation)   │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │    Overrides     │
    │  (Rule Engine)   │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Book Modulation │
    │  (Risk Limits)   │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Decision Report │
    │     (JSON)       │
    └──────────────────┘
    ```

    ### Main Types

    ```python
    @dataclass
    class MarketInputs:
        dt: date
        var_semanal_lineup: float
        percentil_premium: float
        spread_adjusted: float
        z_pace: float
        var_cambio_5d: float
        chicago_percentile: float
        chicago_is_spike: bool
        logistics_flag_active: bool
        logistics_reason: str | None

    @dataclass
    class BookState:
        exposicao_fisica_pct: float
        limite_long_pct: float
        limite_short_pct: float
        hedge_atual_pct: float
        hedge_meta_pct: float

    @dataclass
    class DecisionReport:
        data_referencia: date
        score_fisico: float
        classificacao: str
        recomendacao_fisica: dict
        recomendacao_hedge: dict
        componentes: dict
        overrides_ativos: list
        justificativa: str
    ```
    """
    )


with tab5:
    st.markdown(
        """
    ## Usage API

    ### Basic Usage

    ```python
    from datetime import date
    from src import DecisionEngine, MarketInputs, BookState

    # 1. Create engine (optionally with book state)
    book = BookState(
        exposicao_fisica_pct=30.0,
        limite_long_pct=80.0,
        limite_short_pct=-50.0,
        hedge_atual_pct=45.0,
        hedge_meta_pct=60.0,
    )
    engine = DecisionEngine(book)

    # 2. Prepare market inputs
    inputs = MarketInputs(
        dt=date(2024, 5, 15),
        var_semanal_lineup=8.0,
        percentil_premium=72.0,
        spread_adjusted=5.0,
        z_pace=0.5,
        var_cambio_5d=-0.8,
        chicago_percentile=65.0,
        chicago_is_spike=False,
        logistics_flag_active=False,
        logistics_reason=None,
    )

    # 3. Run engine
    report = engine.run(inputs)

    # 4. Access results
    print(f"Score: {report.score_fisico}")
    print(f"Physical: {report.recomendacao_fisica['acao']}")
    print(f"Hedge: {report.recomendacao_hedge['acao']}")

    # 5. JSON output
    print(report.to_json())
    ```

    ---

    ### Available Functions

    #### Engine
    ```python
    from src import run_decision_engine, DecisionEngine

    # Direct function
    report = run_decision_engine(inputs, book)

    # Class with state
    engine = DecisionEngine(book)
    report = engine.run(inputs)
    ```

    #### Individual Scoring
    ```python
    from src import (
        score_lineup,
        score_premium,
        score_competitiveness,
        score_demand,
        score_cambio,
        compute_score_fisico,
    )

    # Individual scores
    s1 = score_lineup(var_semanal=8.0)      # 0-100
    s2 = score_premium(percentile=72.0)     # 0-100
    s3 = score_competitiveness(spread=5.0)  # 0-100
    s4 = score_demand(z_pace=0.5)           # 0-100
    s5 = score_cambio(var_5d=-0.8)          # 0-100
    ```

    #### Overrides
    ```python
    from src import (
        evaluate_overrides,
        check_queda_conjunta,
        check_armadilha_premio,
        check_logistica,
    )

    # Check specific override
    override = check_queda_conjunta(var_lineup=-15.0, percentil=25.0)
    if override:
        print(f"Override active: {override.type}")
    ```

    ---

    ### Complete JSON Output

    ```json
    {
      "data_referencia": "2024-05-15",
      "score_fisico": 68.5,
      "classificacao": "forte",
      "recomendacao_fisica": {
        "acao": "aumentar",
        "intensidade": "moderada",
        "sizing_pct": 15.0
      },
      "recomendacao_hedge": {
        "acao": "manter",
        "intensidade": "neutra",
        "delta_pp": 0.0
      },
      "componentes": {
        "lineup": {"score": 77.0, "var_semanal": 8.0},
        "premio": {"score": 72.0, "percentil": 72.0},
        "competitividade": {"score": 37.5, "spread": 5.0},
        "demanda": {"score": 66.7, "z_pace": 0.5},
        "cambio": {"score": 63.3, "var_5d": -0.8}
      },
      "overrides_ativos": [],
      "override_dominante": null,
      "modulacao_aplicada": false,
      "modulacao_razao": null,
      "justificativa": "Strong physical (score 68) | ..."
    }
    ```
    """
    )

st.markdown("---")
st.info(
    """
**Tip:** Use the Simulator page to test different scenarios
and see how the engine responds in real-time.
"""
)
