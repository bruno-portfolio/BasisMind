# BasisMind 🌾

[![CI](https://github.com/bruno-portfolio/BasisMind/actions/workflows/ci.yml/badge.svg)](https://github.com/bruno-portfolio/BasisMind/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Basis** (commodity trading term) + **Mind** (intelligence) — A decision support system for physical grain trading operations, transforming scattered market signals into consistent and auditable recommendations.

<img width="1784" height="811" alt="image" src="https://github.com/user-attachments/assets/9ac91985-44f3-40c2-a474-75369976fbf7" />
<img width="1493" height="820" alt="image" src="https://github.com/user-attachments/assets/2f1ff170-c253-492b-9e1f-9f2a38323059" />
<img width="1416" height="874" alt="image" src="https://github.com/user-attachments/assets/8f3caaeb-7f70-40be-b617-e25d0407c7e2" />
<img width="1423" height="865" alt="image" src="https://github.com/user-attachments/assets/7909df82-fa71-46d7-804d-3c09eff62d2f" />
<img width="1419" height="886" alt="image" src="https://github.com/user-attachments/assets/d11f05a9-d2de-4af9-a219-e48514826aa7" />
<img width="971" height="887" alt="image" src="https://github.com/user-attachments/assets/38161f03-dd7f-476a-8a0c-9fb77ec98b60" />

## Overview

The **Decision Engine** standardizes market reading and reduces subjective bias in commodity trading decisions. It formalizes into explicit rules the logic that experienced professionals apply intuitively.

### Key Questions Answered

| Axis | Question |
|------|----------|
| **Physical** | Accelerate sales, hold position, or reduce exposure? |
| **Hedge** | Increase Chicago hedge, hold, or reduce? |

Every recommendation includes a **traceable justification** showing which signals drove the decision.

## Features

- **📊 Weighted Scoring** - Combines 5 market indicators into a single [0-100] score
- **⚡ Override Rules** - 5 rules that dominate scoring in critical market situations
- **📈 Book Modulation** - Adjusts recommendations based on current exposure limits
- **🔍 Full Traceability** - Every decision includes detailed justification
- **🎛️ Interactive Simulator** - Test any scenario in real-time

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          MARKET INPUTS                              │
│   Premium │ Lineup │ Competitiveness │ FX Rate │ Demand │ Chicago  │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        SCORING ENGINE                               │
│   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐           │
│   │ Lineup │ │Premium │ │ Compet │ │ Demand │ │   FX   │           │
│   │  30%   │ │  25%   │ │  20%   │ │  15%   │ │  10%   │           │
│   └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘           │
│       └──────────┴──────────┴──────────┴──────────┘                 │
│                    Aggregated Score [0-100]                         │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        OVERRIDE RULES                               │
│  Logistics │ Joint Drop │ Premium Trap │ Competitiveness │ Spike   │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       BOOK MODULATION                               │
│         Exposure Limits │ Hedge Target │ Effective Sizing           │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       DECISION OUTPUT                               │
│     Physical Recommendation │ Hedge Recommendation │ Justification  │
└─────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/basismind.git
cd basismind

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Run the Dashboard

```bash
streamlit run dashboard/app.py
```

Open **http://localhost:8501** in your browser.

## 📊 Score Components

| Component | Weight | Description |
|-----------|--------|-------------|
| **Lineup** | 30% | Real demand: scheduled vessels for shipment |
| **Premium** | 25% | Price level vs historical (by crop/off-season regime) |
| **Competitiveness** | 20% | Brazil vs US Gulf FOB spread |
| **Demand** | 15% | Export pace vs 5-year average |
| **FX Rate** | 10% | USD/BRL variation (margin modulator) |

## ⚡ Override Rules

Overrides **dominate** the score when triggered:

| Priority | Override | Condition | Action |
|----------|----------|-----------|--------|
| 1 | **Logistics** | Port congestion, strikes | Sell urgently |
| 2 | **Joint Drop** | Lineup ↓ AND Premium ↓ | Reduce exposure |
| 3 | **Premium Trap** | Premium ↑ AND Lineup ↓ | Capture via sale |
| 4 | **Competitiveness** | Spread > +15 USD/ton | Sell |
| 5 | **Chicago Spike** | >5% rise without fundamentals | Hedge, don't buy |

## 📁 Project Structure

```
basismind/
├── src/                      # Core engine (12 modules)
│   ├── config.py             # Constants and thresholds
│   ├── scoring.py            # Scoring engine
│   ├── overrides.py          # Override rules
│   ├── engine.py             # Main integrated engine
│   └── ...
├── dashboard/                # Streamlit dashboard
│   ├── app.py                # Home page
│   └── pages/                # Dashboard pages
│       ├── 1_📊_Dados_Mercado.py
│       ├── 2_🎯_Motor_Decisao.py
│       ├── 3_🔄_Simulador.py
│       ├── 4_📈_Analise.py
│       └── 5_📚_Documentacao.py
├── data/
│   └── mock_generator.py     # Synthetic data generator
├── examples/
│   └── demo.py               # CLI demonstration
└── notebooks/
    └── demo.ipynb            # Jupyter notebook
```

## 💻 Usage Example

```python
from datetime import date
from src import DecisionEngine, MarketInputs, BookState

# Initialize engine with book state
book = BookState(
    exposicao_fisica_pct=30.0,
    limite_long_pct=80.0,
    limite_short_pct=-50.0,
    hedge_atual_pct=45.0,
    hedge_meta_pct=60.0,
)
engine = DecisionEngine(book)

# Prepare market inputs
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

# Run engine
report = engine.run(inputs)

print(f"Score: {report.score_fisico:.1f}")
print(f"Physical: {report.recomendacao_fisica['acao']}")
print(f"Hedge: {report.recomendacao_hedge['acao']}")
```

## 📋 JSON Output

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
  "justificativa": "Strong physical (score 68) | Drivers: lineup strong, premium strong | ..."
}
```

## ⚠️ Limitations

The Decision Engine does **NOT**:
- Predict future prices
- Replace human judgment
- Capture geopolitical events
- Guarantee results

## 🛠️ Tech Stack

- **Python 3.11+**
- **Streamlit** - Interactive dashboard
- **SQLite** - Local storage
- **Pandas** - Data manipulation

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  <b>Built as a portfolio project demonstrating skills in:</b><br>
  Python • Data Engineering • Trading Systems • Decision Support • Streamlit
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-features">Features</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-usage-example">Usage</a>
</p>
