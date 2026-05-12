"""
utils/supabase_client.py
Handles all Supabase connectivity.

Add to .streamlit/secrets.toml:
    [supabase]
    url = "https://xxxxxxxxxxxx.supabase.co"
    key = "your-anon-public-key"
"""

import streamlit as st
import pandas as pd

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


@st.cache_resource(show_spinner=False)
def _get_client():
    """Create and cache the Supabase client."""
    if not SUPABASE_AVAILABLE:
        st.error("supabase-py not installed. Run: pip install supabase")
        return None
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except KeyError:
        st.error(
            "Supabase credentials missing. "
            "Add `[supabase]` block with `url` and `key` to `.streamlit/secrets.toml`."
        )
        return None
    except Exception as e:
        st.error(f"Supabase connection error: {e}")
        return None


def get_data(table: str, filters: dict | None = None) -> pd.DataFrame | None:
    """
    Fetch all rows from a Supabase table and return as a DataFrame.

    Parameters
    ----------
    table   : str   — Supabase table name
    filters : dict  — optional {column: value} equality filters

    Returns
    -------
    pd.DataFrame or None on error
    """
    client = _get_client()
    if client is None:
        return _demo_data()   # fall back to demo data for local dev

    try:
        query = client.table(table).select("*")
        if filters:
            for col, val in filters.items():
                query = query.eq(col, val)
        response = query.execute()
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception as e:
        st.warning(f"Error fetching `{table}`: {e}")
        return _demo_data()


def insert_row(table: str, row: dict) -> bool:
    """Insert a single row into a Supabase table."""
    client = _get_client()
    if client is None:
        return False
    try:
        client.table(table).insert(row).execute()
        return True
    except Exception as e:
        st.error(f"Insert failed: {e}")
        return False


# ── Demo / fallback data ─────────────────────────────────────────────────────
def _demo_data() -> pd.DataFrame:
    """Synthetic dataset for offline development."""
    import numpy as np
    from datetime import datetime, timedelta

    rng = np.random.default_rng(42)
    n = 200

    categories     = ["Cybersecurity", "Financial Fraud", "Data Breach", "Misinformation", "Physical Security"]
    incident_types = ["Ransomware", "Phishing", "DDoS", "Insider Threat", "Supply Chain", "Zero-Day", "Social Engineering"]
    countries      = ["Malaysia", "United States", "China", "Germany", "United Kingdom", "Singapore", "Australia", "India"]
    impacts        = ["Critical", "High", "Medium", "Low"]
    sources        = ["Reuters", "BBC", "BleepingComputer", "Krebs on Security", "The Hacker News", "TechCrunch", "Wired"]
    entities       = ["Government", "Financial Institution", "Healthcare", "Technology Company", "Educational Institution", "Critical Infrastructure"]

    base_date = datetime.now() - timedelta(days=180)
    dates = [base_date + timedelta(days=int(rng.integers(0, 180))) for _ in range(n)]

    summaries = [
        "A major ransomware attack disrupted hospital operations across multiple regions.",
        "State-sponsored hackers breached defence contractor networks stealing sensitive data.",
        "Phishing campaign targeted banking customers resulting in significant financial losses.",
        "Critical infrastructure vulnerability discovered in industrial control systems.",
        "Data leak exposed personal information of millions of users from social platform.",
    ]

    keywords_pool = [
        "ransomware, malware, encryption, bitcoin, hospital",
        "APT, espionage, zero-day, nation-state, defence",
        "phishing, credential, banking, social engineering",
        "ICS, SCADA, vulnerability, critical infrastructure, exploit",
        "data breach, PII, GDPR, social media, leak",
    ]

    return pd.DataFrame({
        "id":               range(1, n + 1),
        "title":            [f"Incident Report #{i}" for i in range(1, n + 1)],
        "publication_date": dates,
        "source":           rng.choice(sources, n),
        "url":              [f"https://example.com/incident-{i}" for i in range(1, n + 1)],
        "summary":          rng.choice(summaries, n),
        "relevant_keywords":rng.choice(keywords_pool, n),
        "category":         rng.choice(categories, n),
        "country":          rng.choice(countries, n),
        "impact":           rng.choice(impacts, n, p=[0.1, 0.3, 0.4, 0.2]),
        "incident_type":    rng.choice(incident_types, n),
        "entity_affected":  rng.choice(entities, n),
        "incident_date":    dates,
    })
