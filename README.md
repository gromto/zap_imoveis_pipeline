# 🏙️ Zap Imóveis Pipeline

End-to-end data pipeline that scrapes real estate listings from Zap Imóveis, processes the data, and create a visualization heatmap using Streamlit.

*DISCLAIMER: This project is intended for learning and portfolio purposes.*

![Heatmap Example](example_gif2.gif)

---

## 🚀 Overview

This project implements a complete data pipeline:

1. **Data Extraction** – Scrapes real estate listings using Selenium and Chromedriver
2. **Data Storage** – Saves raw structured data into local Postgres SQL server
3. **Data Transformation** – Uses dbt to model and clean data
4. **Data Output** – Generates analytics-ready datasets, geospatial files and visualization

---

## 📂 Project Structure

```
.
├── tasks/              # Pipeline tasks (scraping, dbt execution)
├── flows/              # Orchestration logic (Prefect flows)
├── services/           # Main functions used on the pipeline
├── sql/                # Raw SQL queries
├── imoveis_dbt/        # dbt project
├── data/               # Generated data artifacts (ignored in Git)
├── streamlit/          # Streamlit app (Map + Dashboard)
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚙️ Tech Stack

* Python
* Streamlit
* dbt
* Prefect
* GeoJSON
* Selenium / Undetected Chromedrive

---

## ▶️ Running the Pipeline

### 1. Clone the repository

```bash
git clone https://github.com/your-username/zap-imoveis-data-pipeline.git
cd zap-imoveis-data-pipeline
```

### 2. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Fill in required variables (API keys, configs).

---

### 5. Run the pipeline

```bash
python -m flows.complete_pipeline
```

## 🎦 Running visualization (Streamlit)

### 1. change directory to Streamlit folder

```bash
cd streamlit
```

### 2. Streamlit run main.py

```bash
streamlit run main.py
```


## 👨‍💻 Author

Gabriel Romeo Tomaz
Linkedin: https://www.linkedin.com/in/gabrielromeo/
Website: https://gabrielrt.com/
