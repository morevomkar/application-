# Multi-Country Economic Indicators Dashboard (No Graphs)
# File: economic_dashboard.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import os

# Page configuration
st.set_page_config(
    page_title="Global Economic Indicators",
    page_icon="🌍",
    layout="wide"
)

# API Configuration


# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin: 10px 0;
    }
    .country-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 20px 0;
    }
    .indicator-header {
        background-color: #2c3e50;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin: 15px 0;
    }
    .positive {
        color: #28a745;
        font-weight: bold;
    }
    .negative {
        color: #dc3545;
        font-weight: bold;
    }
    .neutral {
        color: #6c757d;
        font-weight: bold;
    }
    .dataframe {
        font-size: 14px;
    }
    .comparison-table {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Data fetching functions
@st.cache_data(ttl=3600)
def fetch_fred_data(series_id, start_date, end_date):
    """Fetch data from FRED API"""
    try:
        if not FRED_API_KEY:
            return None
        fred = Fred(api_key=FRED_API_KEY)
        data = fred.get_series(series_id, start_date, end_date)
        return data
    except Exception as e:
        st.error(f"Error fetching {series_id}: {str(e)}")
        return None

@st.cache_data(ttl=3600)
def fetch_world_bank_data(country_code, indicator):
    """Fetch data from World Bank API"""
    try:
        url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator}"
        params = {
            'format': 'json',
            'per_page': 50,
            'date': '2020:2024'
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 1 and data[1]:
                return data[1]
        return None
    except Exception as e:
        st.error(f"World Bank API Error: {str(e)}")
        return None

def calculate_metrics(data):
    """Calculate key metrics from data"""
    if data is None or len(data) == 0:
        return None
    
    if isinstance(data, pd.Series):
        current = data.iloc[-1]
        previous = data.iloc[-2] if len(data) > 1 else None
        year_ago = data.iloc[-12] if len(data) >= 12 else None
    else:
        # For World Bank data (list of dicts)
        current = data[0]['value'] if data[0]['value'] else None
        previous = data[1]['value'] if len(data) > 1 and data[1]['value'] else None
        year_ago = None
        for item in data:
            if item['value']:
                year_ago = item['value']
                break
    
    if current is None:
        return None
    
    metrics = {
        'current': current,
        'previous': previous,
        'year_ago': year_ago,
        'mom_change': None,
        'yoy_change': None,
        'mom_pct': None,
        'yoy_pct': None
    }
    
    if previous:
        metrics['mom_change'] = current - previous
        metrics['mom_pct'] = ((current - previous) / previous) * 100 if previous != 0 else 0
    
    if year_ago:
        metrics['yoy_change'] = current - year_ago
        metrics['yoy_pct'] = ((current - year_ago) / year_ago) * 100 if year_ago != 0 else 0
    
    return metrics

def format_change(value, is_percentage=False):
    """Format change value with color"""
    if value is None:
        return "N/A"
    
    color_class = "positive" if value > 0 else "negative" if value < 0 else "neutral"
    arrow = "▲" if value > 0 else "▼" if value < 0 else "●"
    
    if is_percentage:
        return f'<span class="{color_class}">{arrow} {abs(value):.2f}%</span>'
    else:
        return f'<span class="{color_class}">{arrow} {abs(value):.2f}</span>'

# Economic indicators configuration
INDICATORS = {
    'US': {
        'CPI': {'fred_id': 'CPIAUCSL', 'name': 'Consumer Price Index'},
        'PPI': {'fred_id': 'PPIACO', 'name': 'Producer Price Index'},
        'Interest Rate': {'fred_id': 'FEDFUNDS', 'name': 'Federal Funds Rate'},
        'Unemployment': {'fred_id': 'UNRATE', 'name': 'Unemployment Rate'},
        'GDP Growth': {'fred_id': 'A191RL1Q225SBEA', 'name': 'GDP Growth Rate'}
    },
    'Europe': {
        'CPI': {'fred_id': 'CP0000EZ19M086NEST', 'name': 'Euro Area CPI'},
        'PPI': {'fred_id': 'PIEAMP01EZM661N', 'name': 'Euro Area PPI'},
        'Interest Rate': {'fred_id': 'ECBDFR', 'name': 'ECB Deposit Rate'},
        'Unemployment': {'fred_id': 'LRHUTTTTEZM156S', 'name': 'Euro Area Unemployment'},
        'GDP Growth': {'fred_id': 'CLVMNACSCAB1GQEA19', 'name': 'Euro Area GDP Growth'}
    },
    'India': {
        'CPI': {'wb_id': 'FP.CPI.TOTL.ZG', 'name': 'CPI Inflation'},
        'Interest Rate': {'wb_id': 'FR.INR.RINR', 'name': 'Real Interest Rate'},
        'GDP Growth': {'wb_id': 'NY.GDP.MKTP.KD.ZG', 'name': 'GDP Growth'},
        'Unemployment': {'wb_id': 'SL.UEM.TOTL.ZS', 'name': 'Unemployment Rate'}
    }
}

# Main app
def main():
    st.title("🌍 Global Economic Indicators Dashboard")
    st.markdown("**Real-time economic data for USA, Europe, and India**")
    
  
    
    # Sidebar settings
    st.sidebar.header("⚙️ Settings")
    
    selected_countries = st.sidebar.multiselect(
        "Select Countries",
        ["US", "Europe", "India"],
        default=["US", "Europe", "India"]
    )
    
    years_back = st.sidebar.slider("Years of Data", 1, 10, 3)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years_back*365)
    
    view_mode = st.sidebar.radio("View Mode", ["Country Comparison", "Indicator Comparison", "Detailed Tables"])
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "💹 CPI & PPI", "💰 Interest Rates", "📈 Full Data"])
    
    # Tab 1: Overview
    with tab1:
        st.header("Economic Indicators Overview")
        
        for country in selected_countries:
            st.markdown(f'<div class="country-header"><h2>🏛️ {country}</h2></div>', unsafe_allow_html=True)
            
            cols = st.columns(3)
            
            indicators = INDICATORS[country]
            col_idx = 0
            
            for indicator_name, indicator_info in indicators.items():
                if col_idx >= 3:
                    cols = st.columns(3)
                    col_idx = 0
                
                with cols[col_idx]:
                    # Fetch data
                    if country in ['US', 'Europe']:
                        data = fetch_fred_data(indicator_info['fred_id'], start_date, end_date)
                    else:  # India
                        data = fetch_world_bank_data('IND', indicator_info.get('wb_id'))
                    
                    metrics = calculate_metrics(data)
                    
                    if metrics:
                        st.markdown(f"**{indicator_info['name']}**")
                        st.metric(
                            label="Current Value",
                            value=f"{metrics['current']:.2f}",
                            delta=f"{metrics['mom_change']:.2f}" if metrics['mom_change'] else None
                        )
                        
                        if metrics['yoy_pct']:
                            st.markdown(f"YoY Change: {format_change(metrics['yoy_pct'], True)}", unsafe_allow_html=True)
                    else:
                        st.info(f"{indicator_info['name']}: Data unavailable")
                
                col_idx += 1
            
            st.markdown("---")
    
    # Tab 2: CPI & PPI Detailed View
    with tab2:
        st.header("💹 Inflation Indicators - CPI & PPI")
        
        for indicator_type in ['CPI', 'PPI']:
            st.markdown(f'<div class="indicator-header"><h3>{indicator_type} - Consumer/Producer Price Index</h3></div>', unsafe_allow_html=True)
            
            comparison_data = []
            
            for country in selected_countries:
                if indicator_type in INDICATORS[country]:
                    indicator_info = INDICATORS[country][indicator_type]
                    
                    if country in ['US', 'Europe']:
                        data = fetch_fred_data(indicator_info['fred_id'], start_date, end_date)
                    else:
                        data = fetch_world_bank_data('IND', indicator_info.get('wb_id'))
                    
                    metrics = calculate_metrics(data)
                    
                    if metrics:
                        comparison_data.append({
                            'Country': country,
                            'Current Value': f"{metrics['current']:.2f}",
                            'MoM Change': f"{metrics['mom_change']:.2f}" if metrics['mom_change'] else "N/A",
                            'MoM %': f"{metrics['mom_pct']:.2f}%" if metrics['mom_pct'] else "N/A",
                            'YoY Change': f"{metrics['yoy_change']:.2f}" if metrics['yoy_change'] else "N/A",
                            'YoY %': f"{metrics['yoy_pct']:.2f}%" if metrics['yoy_pct'] else "N/A",
                            'Previous': f"{metrics['previous']:.2f}" if metrics['previous'] else "N/A",
                            'Year Ago': f"{metrics['year_ago']:.2f}" if metrics['year_ago'] else "N/A"
                        })
            
            if comparison_data:
                df = pd.DataFrame(comparison_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.warning(f"No {indicator_type} data available for selected countries")
            
            st.markdown("---")
    
    # Tab 3: Interest Rates
    with tab3:
        st.header("💰 Interest Rates Comparison")
        
        st.markdown('<div class="indicator-header"><h3>Central Bank Policy Rates</h3></div>', unsafe_allow_html=True)
        
        comparison_data = []
        
        for country in selected_countries:
            if 'Interest Rate' in INDICATORS[country]:
                indicator_info = INDICATORS[country]['Interest Rate']
                
                if country in ['US', 'Europe']:
                    data = fetch_fred_data(indicator_info['fred_id'], start_date, end_date)
                else:
                    data = fetch_world_bank_data('IND', indicator_info.get('wb_id'))
                
                metrics = calculate_metrics(data)
                
                if metrics:
                    comparison_data.append({
                        'Country': country,
                        'Rate Name': indicator_info['name'],
                        'Current Rate (%)': f"{metrics['current']:.2f}%",
                        'Previous (%)': f"{metrics['previous']:.2f}%" if metrics['previous'] else "N/A",
                        'Change (bps)': f"{metrics['mom_change']*100:.0f}" if metrics['mom_change'] else "N/A",
                        'Year Ago (%)': f"{metrics['year_ago']:.2f}%" if metrics['year_ago'] else "N/A",
                        'YoY Change (bps)': f"{metrics['yoy_change']*100:.0f}" if metrics['yoy_change'] else "N/A"
                    })
        
        if comparison_data:
            df = pd.DataFrame(comparison_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Interest rate analysis
            st.subheader("📊 Rate Analysis")
            cols = st.columns(len(selected_countries))
            
            for idx, country in enumerate(selected_countries):
                with cols[idx]:
                    country_data = [d for d in comparison_data if d['Country'] == country]
                    if country_data:
                        data = country_data[0]
                        st.markdown(f"**{country}**")
                        st.info(f"Current: {data['Current Rate (%)']}")
                        
                        try:
                            change = float(data['Change (bps)'].replace(' bps', ''))
                            if change > 0:
                                st.success(f"↑ Increased by {abs(change):.0f} bps")
                            elif change < 0:
                                st.error(f"↓ Decreased by {abs(change):.0f} bps")
                            else:
                                st.info("● No change")
                        except:
                            pass
        else:
            st.warning("No interest rate data available")
    
    # Tab 4: Full Data Tables
    with tab4:
        st.header("📈 Complete Economic Data")
        
        for country in selected_countries:
            st.markdown(f'<div class="country-header"><h2>{country} - All Indicators</h2></div>', unsafe_allow_html=True)
            
            all_data = []
            
            for indicator_name, indicator_info in INDICATORS[country].items():
                if country in ['US', 'Europe']:
                    data = fetch_fred_data(indicator_info['fred_id'], start_date, end_date)
                else:
                    data = fetch_world_bank_data('IND', indicator_info.get('wb_id'))
                
                metrics = calculate_metrics(data)
                
                if metrics:
                    all_data.append({
                        'Indicator': indicator_info['name'],
                        'Current': f"{metrics['current']:.2f}",
                        'Previous': f"{metrics['previous']:.2f}" if metrics['previous'] else "N/A",
                        'MoM Change': f"{metrics['mom_change']:.2f}" if metrics['mom_change'] else "N/A",
                        'MoM %': f"{metrics['mom_pct']:.2f}%" if metrics['mom_pct'] else "N/A",
                        'Year Ago': f"{metrics['year_ago']:.2f}" if metrics['year_ago'] else "N/A",
                        'YoY Change': f"{metrics['yoy_change']:.2f}" if metrics['yoy_change'] else "N/A",
                        'YoY %': f"{metrics['yoy_pct']:.2f}%" if metrics['yoy_pct'] else "N/A"
                    })
            
            if all_data:
                df = pd.DataFrame(all_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    label=f"📥 Download {country} Data",
                    data=csv,
                    file_name=f"{country}_economic_data_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning(f"No data available for {country}")
            
            st.markdown("---")
    
    # Sidebar information
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    ### 📊 Data Sources
    - **US & Europe**: FRED API
    - **India**: World Bank API
    
    ### 📌 Indicators
    - **CPI**: Consumer Price Index
    - **PPI**: Producer Price Index  
    - **Interest Rates**: Central Bank Rates
    - **GDP**: Growth Rates
    - **Unemployment**: Labor Market
    
    ### 🔄 Updates
    Data refreshed every hour
    """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>Global Economic Dashboard v1.0 | Data: FRED & World Bank APIs</p>
        <p>Last updated: {}</p>
    </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)

if __name__ == "__main__":
    main()


# ==============================================================================
# GITHUB REPOSITORY FILES
# ==============================================================================
"""
Create these files in your repository:

--- requirements.txt ---
streamlit==1.28.0
pandas==2.0.3
fredapi==0.5.1
requests==2.31.0

--- README.md ---
# Global Economic Indicators Dashboard

Multi-country economic dashboard showing CPI, PPI, Interest Rates for USA, Europe, and India.

## Features
- Real-time data from FRED and World Bank APIs
- Compare indicators across countries
- No graphs - pure data tables and metrics
- Download data as CSV
- MoM and YoY calculations

## Setup

1. Install: `pip install -r requirements.txt`
2. Get FRED API key: https://fred.stlouisfed.org/
3. Set environment: `export FRED_API_KEY=your_key`
4. Run: `streamlit run economic_dashboard.py`

## Deployment (Streamlit Cloud)

1. Push to GitHub
2. Deploy on https://share.streamlit.io/
3. Add FRED_API_KEY in Secrets
4. No World Bank API key needed (public API)

--- .gitignore ---
__pycache__/
*.pyc
.env
.streamlit/secrets.toml
venv/
*.csv

--- .streamlit/secrets.toml ---
# For local development only - DO NOT commit to GitHub
FRED_API_KEY = "your_api_key_here"
"""
