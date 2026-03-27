# Rappi AI Intelligence Engine

AI-powered operational analytics and competitive intelligence platform for Rappi.

## Cases

- **Case 1**: Conversational bot + automatic insights over Rappi operational data (9 countries, 964 zones, 13 metrics, 8-week rolling window)
- **Case 2**: Competitive scraping system (Rappi vs UberEats vs DiDi Food in Mexico) + insight report

## Stack

- **Python 3.10+**
- **Streamlit** - Interactive UI
- **OpenRouter** - LLM gateway (Claude, GPT-4o, Gemini, Llama)
- **Pandas** - Data processing
- **Plotly** - Visualizations
- **Playwright** - Web scraping

## Setup

```bash
# Clone the repo
git clone <repo-url>
cd rappi-ai-engine

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (for Case 2)
playwright install chromium

# Configure environment
cp .env.example .env
# Edit .env and add your OpenRouter API key

# Place the Excel data file
# Copy the .xlsx file to data/raw/
```

## Run

```bash
streamlit run app/main.py
```

## Project Structure

```
rappi-ai-engine/
├── app/
│   ├── main.py              # Streamlit entry point
│   ├── config.py            # Global configuration
│   ├── chatbot/             # Conversational AI (Case 1)
│   │   ├── engine.py        # Core chatbot logic
│   │   ├── prompts.py       # System prompts and templates
│   │   └── memory.py        # Conversation memory
│   ├── insights/            # Automatic insights (Case 1)
│   │   ├── analyzer.py      # Insight detection engine
│   │   └── report.py        # Report generation
│   ├── scraping/            # Web scraping (Case 2)
│   │   ├── base.py          # Base scraper class
│   │   ├── rappi.py         # Rappi scraper
│   │   ├── ubereats.py      # UberEats scraper
│   │   ├── didifood.py      # DiDi Food scraper
│   │   └── addresses.py     # Representative addresses
│   ├── competitive/         # Competitive analysis (Case 2)
│   │   ├── analysis.py      # Cross-platform comparison
│   │   └── report.py        # Competitive report
│   ├── data/                # Data loading and queries
│   │   ├── loader.py        # Excel/CSV loading
│   │   ├── metrics.py       # Metric definitions
│   │   └── queries.py       # DataFrame query functions
│   └── utils/
│       └── llm.py           # OpenRouter LLM client
├── data/
│   ├── raw/                 # Original Excel file (not tracked)
│   └── processed/           # Generated CSVs
├── outputs/                 # Generated reports
├── notebooks/               # Exploration notebooks
├── .env.example
├── requirements.txt
└── setup.py
```

## Architecture

_TODO: Architecture diagram and detailed design documentation._

## Cost Analysis

_TODO: LLM token usage estimates and cost projections per model._

## License

Internal - Rappi AI Engineer Technical Assessment
