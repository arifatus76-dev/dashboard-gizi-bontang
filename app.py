"""
Dashboard Interaktif Status Gizi Balita - Kota Bontang
======================================================
Versi Multi-Tahun (2023, 2024, 2025, dst.)

Cara menjalankan:
    streamlit run dashboard_gizi_streamlit.py

PENTING: Jalankan dengan 'streamlit run', BUKAN 'python'
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# ============================================================================
# KONFIGURASI HALAMAN
# ============================================================================
st.set_page_config(
    page_title="Dashboard Gizi Balita - Kota Bontang",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS
# ============================================================================
st.markdown("""
<style>
    .main .block-container {
        padding: 1rem 2rem 2rem 2rem;
        max-width: 1400px;
    }
    
    .dashboard-header {
        background: linear-gradient(135deg, #1E3A5F 0%, #2E5A88 50%, #3B82A0 100%);
        padding: 1.5rem 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(30, 58, 95, 0.3);
    }
    
    .dashboard-header h1 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
    }
    
    .dashboard-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    
    .section-header {
        font-size: 1.25rem;
        font-weight: 700;
        color: #1E293B;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #2E5A88;
    }
    
    .info-card {
        background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%);
        border: 1px solid #7DD3FC;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(14, 165, 233, 0.1);
    }
    
    .year-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    
    .year-2023 { background: #DBEAFE; color: #1E40AF; }
    .year-2024 { background: #D1FAE5; color: #065F46; }
    .year-2025 { background: #FEF3C7; color: #92400E; }
    .year-2026 { background: #F3E8FF; color: #6B21A8; }
    
    /* Styling untuk metric cards */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    
    [data-testid="stMetric"]:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
        transition: all 0.2s ease;
    }
    
    [data-testid="stMetricLabel"] {
        font-weight: 600 !important;
        color: #475569 !important;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        color: #1E293B !important;
    }
    
    /* Caption styling */
    .stCaption {
        color: #64748B !important;
        font-size: 0.85rem !important;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# FUNGSI LOAD DATA
# ============================================================================
@st.cache_data
def load_data(file_path):
    """Load data dari file CSV dengan berbagai encoding"""
    encodings = ['utf-8', 'cp1252', 'latin1', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            return df
        except:
            continue
    
    df = pd.read_csv(file_path, encoding='utf-8', errors='replace')
    return df

def process_data(df):
    """Proses dan bersihkan data"""
    # Bersihkan data dari baris yang tidak valid
    df = df[~df['Kelurahan'].astype(str).str.contains(r'\[', na=False)]
    df = df[~df['Kecamatan'].astype(str).str.contains(r'\[', na=False)]
    df = df[~df['Puskesmas'].astype(str).str.contains(r'\[', na=False)]
    
    # Konversi kolom numerik
    numeric_cols = [
        'Sasaran_Balita', 'Balita_Ditimbang', 'Balita_Bulan_Ini',
        'Jml_Balita_Stunting', 'Pct_Balita_Stunting',
        'Jml_Balita_Wasting', 'Pct_Balita_Wasting',
        'Jml_Balita_Overweight', 'Pct_Balita_Overweight',
        'Jml_Balita_Underweight', 'Pct_Balita_Underweight',
        'Jml_Gizi_Buruk_Balita_6_59_Bulan'
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Konversi tahun ke integer
    if 'Tahun' in df.columns:
        df['Tahun'] = pd.to_numeric(df['Tahun'], errors='coerce').fillna(2025).astype(int)
    
    # Tambah kolom Bulan_Num untuk sorting
    bulan_order = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                   'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    if 'Bulan' in df.columns:
        df['Bulan_Num'] = df['Bulan'].apply(lambda x: bulan_order.index(x) + 1 if x in bulan_order else 0)
    
    return df

def format_number(num):
    """Format angka dengan pemisah ribuan Indonesia"""
    if pd.isna(num):
        return "0"
    return f"{num:,.0f}".replace(",", ".")

def format_pct(num):
    """Format persentase dengan format Indonesia (koma sebagai desimal)"""
    if pd.isna(num):
        return "0,00%"
    return f"{num:.2f}%".replace(".", ",")

def get_latest_data(df):
    """Ambil data terbaru per kelurahan per tahun"""
    if 'Waktu_Input' in df.columns:
        df['Waktu_Input'] = pd.to_datetime(df['Waktu_Input'], errors='coerce')
        return df.sort_values('Waktu_Input').groupby(['Kelurahan', 'Tahun']).last().reset_index()
    elif 'Bulan_Num' in df.columns:
        return df.sort_values('Bulan_Num').groupby(['Kelurahan', 'Tahun']).last().reset_index()
    else:
        return df.groupby(['Kelurahan', 'Tahun']).last().reset_index()

# ============================================================================
# FUNGSI CHART
# ============================================================================
def create_gauge_chart(value, title, max_val=30, threshold_warning=14, threshold_danger=20):
    """Buat gauge chart untuk KPI dengan format Indonesia"""
    if pd.isna(value):
        value = 0
    
    if value < threshold_warning:
        color = "#16A34A"
        status = "Baik"
    elif value < threshold_danger:
        color = "#F59E0B"
        status = "Sedang"
    else:
        color = "#DC2626"
        status = "Tinggi"
    
    # Format angka Indonesia (koma sebagai desimal)
    value_formatted = f"{value:.2f}".replace(".", ",") + "%"
    
    fig = go.Figure(go.Indicator(
        mode="gauge",
        value=value,
        title={'text': f"{title}<br><span style='font-size:12px;color:{color}'>{status}</span>", 
               'font': {'size': 14, 'color': '#64748B'}},
        gauge={
            'axis': {'range': [0, max_val], 'tickwidth': 1},
            'bar': {'color': color, 'thickness': 0.75},
            'bgcolor': '#F1F5F9',
            'borderwidth': 0,
            'steps': [
                {'range': [0, threshold_warning], 'color': '#DCFCE7'},
                {'range': [threshold_warning, threshold_danger], 'color': '#FEF3C7'},
                {'range': [threshold_danger, max_val], 'color': '#FEE2E2'}
            ]
        }
    ))
    
    # Tambahkan angka dengan format Indonesia sebagai annotation
    fig.add_annotation(
        x=0.5, y=0.25,
        text=value_formatted,
        font=dict(size=32, color='#1E293B'),
        showarrow=False,
        xref="paper", yref="paper"
    )
    
    fig.update_layout(
        height=180,
        margin=dict(l=20, r=20, t=50, b=10),
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def create_trend_line_chart(df, indicator_col, title):
    """Buat line chart trend bulanan per tahun"""
    trend_data = df.groupby(['Tahun', 'Bulan', 'Bulan_Num']).agg({
        'Balita_Ditimbang': 'sum',
        'Jml_Balita_Stunting': 'sum',
        'Jml_Balita_Wasting': 'sum',
        'Jml_Balita_Overweight': 'sum',
        'Jml_Balita_Underweight': 'sum'
    }).reset_index()
    
    trend_data = trend_data.sort_values(['Tahun', 'Bulan_Num'])
    
    # Hitung persentase
    trend_data['Pct_Stunting'] = (trend_data['Jml_Balita_Stunting'] / trend_data['Balita_Ditimbang'] * 100).round(1)
    trend_data['Pct_Wasting'] = (trend_data['Jml_Balita_Wasting'] / trend_data['Balita_Ditimbang'] * 100).round(1)
    trend_data['Pct_Overweight'] = (trend_data['Jml_Balita_Overweight'] / trend_data['Balita_Ditimbang'] * 100).round(1)
    trend_data['Pct_Underweight'] = (trend_data['Jml_Balita_Underweight'] / trend_data['Balita_Ditimbang'] * 100).round(1)
    
    fig = go.Figure()
    
    colors = {2023: '#3B82F6', 2024: '#10B981', 2025: '#EF4444', 2026: '#8B5CF6', 2027: '#F59E0B'}
    
    for tahun in sorted(trend_data['Tahun'].unique()):
        data_tahun = trend_data[trend_data['Tahun'] == tahun]
        color = colors.get(tahun, '#64748B')
        
        fig.add_trace(go.Scatter(
            x=data_tahun['Bulan'],
            y=data_tahun[indicator_col],
            mode='lines+markers',
            name=str(tahun),
            line=dict(color=color, width=3),
            marker=dict(size=8),
            hovertemplate=f'<b>{tahun}</b><br>Bulan: %{{x}}<br>Prevalensi: %{{y:.1f}}%<extra></extra>'
        ))
    
    # Target line
    target_val = 14 if 'Stunting' in indicator_col else 5
    fig.add_hline(y=target_val, line_dash="dash", line_color="green",
                  annotation_text=f"Target {target_val}%", annotation_position="right")
    
    fig.update_layout(
        title=title,
        height=400,
        xaxis_title="Bulan",
        yaxis_title="Prevalensi (%)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode='x unified',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    fig.update_xaxes(showgrid=True, gridcolor='#E2E8F0')
    fig.update_yaxes(showgrid=True, gridcolor='#E2E8F0')
    
    return fig

def create_year_comparison_chart(df):
    """Buat chart perbandingan antar tahun"""
    yearly_data = df.groupby('Tahun').agg({
        'Balita_Ditimbang': 'sum',
        'Jml_Balita_Stunting': 'sum',
        'Jml_Balita_Wasting': 'sum',
        'Jml_Balita_Overweight': 'sum',
        'Jml_Balita_Underweight': 'sum'
    }).reset_index()
    
    yearly_data['Pct_Stunting'] = (yearly_data['Jml_Balita_Stunting'] / yearly_data['Balita_Ditimbang'] * 100).round(2)
    yearly_data['Pct_Wasting'] = (yearly_data['Jml_Balita_Wasting'] / yearly_data['Balita_Ditimbang'] * 100).round(2)
    yearly_data['Pct_Overweight'] = (yearly_data['Jml_Balita_Overweight'] / yearly_data['Balita_Ditimbang'] * 100).round(2)
    yearly_data['Pct_Underweight'] = (yearly_data['Jml_Balita_Underweight'] / yearly_data['Balita_Ditimbang'] * 100).round(2)
    
    # Fungsi format Indonesia untuk label
    def fmt_id(x):
        return f'{x:.2f}%'.replace('.', ',')
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(name='Stunting', x=yearly_data['Tahun'].astype(str), y=yearly_data['Pct_Stunting'], 
                         marker_color='#DC2626', text=yearly_data['Pct_Stunting'].apply(fmt_id),
                         textposition='outside'))
    fig.add_trace(go.Bar(name='Wasting', x=yearly_data['Tahun'].astype(str), y=yearly_data['Pct_Wasting'],
                         marker_color='#F59E0B', text=yearly_data['Pct_Wasting'].apply(fmt_id),
                         textposition='outside'))
    fig.add_trace(go.Bar(name='Overweight', x=yearly_data['Tahun'].astype(str), y=yearly_data['Pct_Overweight'],
                         marker_color='#0891B2', text=yearly_data['Pct_Overweight'].apply(fmt_id),
                         textposition='outside'))
    fig.add_trace(go.Bar(name='Underweight', x=yearly_data['Tahun'].astype(str), y=yearly_data['Pct_Underweight'],
                         marker_color='#7C3AED', text=yearly_data['Pct_Underweight'].apply(fmt_id),
                         textposition='outside'))
    
    fig.add_hline(y=14, line_dash="dash", line_color="green", annotation_text="Target Stunting 14%")
    
    fig.update_layout(
        title='📊 Perbandingan Prevalensi Antar Tahun',
        barmode='group',
        height=400,
        xaxis_title="Tahun",
        yaxis_title="Prevalensi (%)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig, yearly_data

# ============================================================================
# SIDEBAR
# ============================================================================
def create_sidebar(df):
    """Buat sidebar dengan filter interaktif"""
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h2 style="color: #0C4A6E; margin: 0;">🔍 Filter Data</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
    # Filter Tahun
    tahun_list = sorted(df['Tahun'].unique(), reverse=True)
    
    st.sidebar.markdown("### 📅 Periode")
    
    year_mode = st.sidebar.radio(
        "Mode Tahun",
        ["Satu Tahun", "Bandingkan Tahun", "Semua Tahun"],
        horizontal=True,
        help="Pilih mode untuk menampilkan data satu tahun, membandingkan beberapa tahun, atau semua tahun"
    )
    
    if year_mode == "Satu Tahun":
        selected_tahun = [st.sidebar.selectbox("Pilih Tahun", options=tahun_list)]
    elif year_mode == "Bandingkan Tahun":
        selected_tahun = st.sidebar.multiselect(
            "Pilih Tahun",
            options=tahun_list,
            default=tahun_list[:min(2, len(tahun_list))]
        )
    else:
        selected_tahun = tahun_list
    
    # Filter Bulan
    bulan_order = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                   'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    bulan_available = [b for b in bulan_order if b in df['Bulan'].unique()]
    
    selected_bulan = st.sidebar.multiselect(
        "🗓️ Bulan",
        options=bulan_available,
        default=bulan_available
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🏘️ Wilayah")
    
    # Filter Kecamatan
    kecamatan_list = sorted(df['Kecamatan'].dropna().unique())
    selected_kecamatan = st.sidebar.multiselect(
        "Kecamatan",
        options=kecamatan_list,
        default=kecamatan_list
    )
    
    # Filter Puskesmas
    if selected_kecamatan:
        puskesmas_filtered = df[df['Kecamatan'].isin(selected_kecamatan)]['Puskesmas'].dropna().unique()
        puskesmas_list = sorted(puskesmas_filtered)
    else:
        puskesmas_list = sorted(df['Puskesmas'].dropna().unique())
    
    selected_puskesmas = st.sidebar.multiselect(
        "Puskesmas",
        options=puskesmas_list,
        default=puskesmas_list
    )
    
    st.sidebar.markdown("---")
    
    # Info data
    st.sidebar.markdown("### 📊 Info Data")
    tahun_str = ', '.join(map(str, sorted(tahun_list)))
    st.sidebar.info(f"""
    **Tahun tersedia:** {tahun_str}
    
    **Total record:** {len(df):,}
    
    **Kelurahan:** {df['Kelurahan'].nunique()}
    """)
    
    if st.sidebar.button("🔄 Reset Filter", use_container_width=True):
        st.rerun()
    
    return selected_tahun, selected_bulan, selected_kecamatan, selected_puskesmas, year_mode

def filter_data(df, tahun, bulan, kecamatan, puskesmas):
    """Filter dataframe berdasarkan pilihan"""
    filtered = df.copy()
    
    if tahun:
        filtered = filtered[filtered['Tahun'].isin(tahun)]
    if bulan:
        filtered = filtered[filtered['Bulan'].isin(bulan)]
    if kecamatan:
        filtered = filtered[filtered['Kecamatan'].isin(kecamatan)]
    if puskesmas:
        filtered = filtered[filtered['Puskesmas'].isin(puskesmas)]
    
    return filtered

# ============================================================================
# TAB OVERVIEW
# ============================================================================
def render_overview(df, year_mode):
    """Render tab overview"""
    
    # OPSI 1: Gunakan SEMUA data (kumulatif semua bulan)
    df_all = df.copy()
    
    # Hitung KPI dari semua data
    total_ditimbang = df_all['Balita_Ditimbang'].sum()
    total_stunting = df_all['Jml_Balita_Stunting'].sum()
    total_wasting = df_all['Jml_Balita_Wasting'].sum()
    total_overweight = df_all['Jml_Balita_Overweight'].sum()
    total_underweight = df_all['Jml_Balita_Underweight'].sum()
    total_gizi_buruk = df_all['Jml_Gizi_Buruk_Balita_6_59_Bulan'].sum()
    
    # Gunakan WEIGHTED AVERAGE untuk persentase (sama dengan cara hitung Excel)
    pct_stunting = round((total_stunting / total_ditimbang) * 100, 2) if total_ditimbang > 0 else 0
    pct_wasting = round((total_wasting / total_ditimbang) * 100, 2) if total_ditimbang > 0 else 0
    pct_overweight = round((total_overweight / total_ditimbang) * 100, 2) if total_ditimbang > 0 else 0
    pct_underweight = round((total_underweight / total_ditimbang) * 100, 2) if total_ditimbang > 0 else 0
    
    # Info periode
    tahun_list = sorted(df['Tahun'].unique())
    badges = ''.join([f'<span class="year-badge year-{t}">{t}</span>' for t in tahun_list])
    
    st.markdown(f"""
    <div class="info-card">
        <strong>📅 Periode:</strong> {badges}
        &nbsp;|&nbsp;
        <strong>📊 Kelurahan:</strong> {df['Kelurahan'].nunique()}
        &nbsp;|&nbsp;
        <strong>🏥 Puskesmas:</strong> {df['Puskesmas'].nunique()}
    </div>
    """, unsafe_allow_html=True)
    
    # KPI Cards
    st.markdown('<div class="section-header">📊 Indikator Utama</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("👶 Balita Ditimbang", format_number(total_ditimbang))
    with col2:
        st.metric("📏 Stunting", format_pct(pct_stunting))
        st.caption(f"{format_number(total_stunting)} balita")
    with col3:
        st.metric("⚖️ Wasting", format_pct(pct_wasting))
        st.caption(f"{format_number(total_wasting)} balita")
    with col4:
        st.metric("📈 Overweight", format_pct(pct_overweight))
        st.caption(f"{format_number(total_overweight)} balita")
    with col5:
        st.metric("⬇️ Underweight", format_pct(pct_underweight))
        st.caption(f"{format_number(total_underweight)} balita")
    with col6:
        st.metric("🚨 Gizi Buruk", format_number(total_gizi_buruk))
        st.caption("(6-59 Bulan)")
    
    # Gauge Charts
    st.markdown('<div class="section-header">🎯 Status Terhadap Target</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.plotly_chart(create_gauge_chart(pct_stunting, "Stunting", 35, 14, 20), use_container_width=True)
    with col2:
        st.plotly_chart(create_gauge_chart(pct_wasting, "Wasting", 15, 5, 10), use_container_width=True)
    with col3:
        st.plotly_chart(create_gauge_chart(pct_overweight, "Overweight", 15, 5, 10), use_container_width=True)
    with col4:
        st.plotly_chart(create_gauge_chart(pct_underweight, "Underweight", 25, 10, 15), use_container_width=True)
    
    # Perbandingan Tahun
    if len(df['Tahun'].unique()) > 1:
        st.markdown('<div class="section-header">📈 Perbandingan Antar Tahun</div>', unsafe_allow_html=True)
        fig, yearly_data = create_year_comparison_chart(df)
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB TREND
# ============================================================================
def render_trend(df):
    """Render tab trend"""
    
    st.markdown('<div class="section-header">📈 Trend Bulanan</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        indicator = st.selectbox(
            "Pilih Indikator",
            ["Stunting", "Wasting", "Overweight", "Underweight"]
        )
    
    indicator_col = f'Pct_{indicator}'
    
    with col1:
        fig = create_trend_line_chart(df, indicator_col, f'📈 Trend Prevalensi {indicator} per Bulan')
        st.plotly_chart(fig, use_container_width=True)
    
    # Area chart
    st.markdown('<div class="section-header">📊 Jumlah Kasus per Bulan</div>', unsafe_allow_html=True)
    
    trend_data = df.groupby(['Tahun', 'Bulan', 'Bulan_Num']).agg({
        f'Jml_Balita_{indicator}': 'sum'
    }).reset_index().sort_values(['Tahun', 'Bulan_Num'])
    
    fig = px.area(
        trend_data,
        x='Bulan',
        y=f'Jml_Balita_{indicator}',
        color='Tahun',
        title=f'📊 Jumlah Kasus {indicator} per Bulan',
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    
    fig.update_layout(height=350, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB DISTRIBUSI
# ============================================================================
def render_distribution(df):
    """Render tab distribusi"""
    
    st.markdown('<div class="section-header">🗺️ Distribusi per Wilayah</div>', unsafe_allow_html=True)
    
    df_latest = get_latest_data(df)
    
    col1, col2 = st.columns(2)
    
    with col1:
        puskesmas_data = df_latest.groupby('Puskesmas').agg({
            'Balita_Ditimbang': 'sum',
            'Jml_Balita_Stunting': 'sum'
        }).reset_index()
        puskesmas_data['Pct_Stunting'] = (puskesmas_data['Jml_Balita_Stunting'] / puskesmas_data['Balita_Ditimbang'] * 100).round(1)
        puskesmas_data = puskesmas_data.sort_values('Pct_Stunting', ascending=True)
        
        fig = px.bar(puskesmas_data, x='Pct_Stunting', y='Puskesmas', orientation='h',
                     title='📊 Prevalensi Stunting per Puskesmas',
                     color='Pct_Stunting', color_continuous_scale=['#16A34A', '#F59E0B', '#DC2626'],
                     text='Pct_Stunting')
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.add_vline(x=14, line_dash="dash", line_color="green", annotation_text="Target 14%")
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        treemap_data = df_latest[['Kecamatan', 'Kelurahan', 'Jml_Balita_Stunting', 'Pct_Balita_Stunting']].copy()
        treemap_data = treemap_data[treemap_data['Jml_Balita_Stunting'] > 0]
        
        if not treemap_data.empty:
            fig = px.treemap(treemap_data, path=['Kecamatan', 'Kelurahan'], values='Jml_Balita_Stunting',
                           color='Pct_Balita_Stunting', color_continuous_scale=['#16A34A', '#F59E0B', '#DC2626'],
                           range_color=[10, 30], title='🗺️ Distribusi Stunting per Kelurahan')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # Scatter plot
    st.markdown('<div class="section-header">🔍 Analisis Korelasi</div>', unsafe_allow_html=True)
    
    # Warna kontras untuk setiap kecamatan
    color_kecamatan = {
        'BONTANG UTARA': '#2563EB',    # Biru
        'BONTANG BARAT': '#16A34A',    # Hijau
        'BONTANG SELATAN': '#DC2626'   # Merah
    }
    
    fig = px.scatter(df_latest, x='Pct_Balita_Stunting', y='Pct_Balita_Wasting', size='Balita_Ditimbang',
                     color='Kecamatan', hover_name='Kelurahan',
                     color_discrete_map=color_kecamatan,
                     title='📊 Korelasi Stunting vs Wasting per Kelurahan',
                     labels={'Pct_Balita_Stunting': 'Stunting (%)', 'Pct_Balita_Wasting': 'Wasting (%)'})
    fig.add_hline(y=5, line_dash="dash", line_color="orange", opacity=0.5)
    fig.add_vline(x=14, line_dash="dash", line_color="red", opacity=0.5)
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB PERBANDINGAN
# ============================================================================
def render_comparison(df):
    """Render tab perbandingan"""
    
    st.markdown('<div class="section-header">⚖️ Perbandingan Antar Wilayah</div>', unsafe_allow_html=True)
    
    df_latest = get_latest_data(df)
    kelurahan_list = sorted(df_latest['Kelurahan'].unique())
    
    col1, col2 = st.columns(2)
    
    with col1:
        wilayah1 = st.selectbox("Pilih Wilayah 1", options=kelurahan_list, key='w1')
    with col2:
        wilayah2 = st.selectbox("Pilih Wilayah 2", options=[k for k in kelurahan_list if k != wilayah1], key='w2')
    
    data1 = df_latest[df_latest['Kelurahan'] == wilayah1].iloc[0]
    data2 = df_latest[df_latest['Kelurahan'] == wilayah2].iloc[0]
    
    categories = ['Stunting', 'Wasting', 'Overweight', 'Underweight']
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[data1['Pct_Balita_Stunting'], data1['Pct_Balita_Wasting'], data1['Pct_Balita_Overweight'], data1['Pct_Balita_Underweight']],
        theta=categories, fill='toself', name=wilayah1, line_color='#2563EB', fillcolor='rgba(37,99,235,0.25)'
    ))
    fig.add_trace(go.Scatterpolar(
        r=[data2['Pct_Balita_Stunting'], data2['Pct_Balita_Wasting'], data2['Pct_Balita_Overweight'], data2['Pct_Balita_Underweight']],
        theta=categories, fill='toself', name=wilayah2, line_color='#16A34A', fillcolor='rgba(22,163,74,0.25)'
    ))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 35])),
                      title=f'📊 Perbandingan {wilayah1} vs {wilayah2}', height=450)
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# MAIN APP
# ============================================================================
def main():
    st.markdown("""
    <div class="dashboard-header">
        <h1>🏥 Dashboard Status Gizi Balita</h1>
        <p>Dinas Kesehatan Kota Bontang - Provinsi Kalimantan Timur</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        df = load_data('Database_Gizi_Clean.csv')
        df = process_data(df)
    except FileNotFoundError:
        st.error("⚠️ File `Database_Gizi_Clean.csv` tidak ditemukan. Pastikan file ada di folder yang sama.")
        st.stop()
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.stop()
    
    selected_tahun, selected_bulan, selected_kecamatan, selected_puskesmas, year_mode = create_sidebar(df)
    df_filtered = filter_data(df, selected_tahun, selected_bulan, selected_kecamatan, selected_puskesmas)
    
    if len(df_filtered) == 0:
        st.warning("⚠️ Tidak ada data yang sesuai dengan filter.")
        st.stop()
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Trend", "🗺️ Distribusi", "⚖️ Perbandingan"])
    
    with tab1:
        render_overview(df_filtered, year_mode)
    with tab2:
        render_trend(df_filtered)
    with tab3:
        render_distribution(df_filtered)
    with tab4:
        render_comparison(df_filtered)
    
    st.markdown("---")
    st.markdown('<div style="text-align:center;color:#64748B;font-size:1rem;">📊 Dashboard Status Gizi Balita - Dinas Kesehatan Kota Bontang | © 2025</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
