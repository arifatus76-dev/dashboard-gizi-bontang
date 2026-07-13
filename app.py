"""
Dashboard Interaktif Status Gizi Balita - Kota Bontang
======================================================
Versi Multi-Tahun (2023, 2024, 2025, dst.)
Optimasi memori untuk Streamlit Community Cloud (max 1 GB RAM)

Cara menjalankan:
    streamlit run app.py

PENTING: Jalankan dengan 'streamlit run', BUKAN 'python'
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gc

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
    
    .dashboard-header h1 { margin: 0; font-size: 1.8rem; font-weight: 700; }
    .dashboard-header p { margin: 0.5rem 0 0 0; opacity: 0.9; }
    
    .section-header {
        font-size: 1.25rem; font-weight: 700; color: #1E293B;
        margin: 1.5rem 0 1rem 0; padding-bottom: 0.5rem;
        border-bottom: 3px solid #2E5A88;
    }
    
    .info-card {
        background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%);
        border: 1px solid #7DD3FC; border-radius: 12px;
        padding: 1rem 1.25rem; margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(14, 165, 233, 0.1);
    }
    
    .year-badge {
        display: inline-block; padding: 0.25rem 0.75rem;
        border-radius: 20px; font-size: 0.85rem; font-weight: 600;
        margin-right: 0.5rem;
    }
    .year-2023 { background: #DBEAFE; color: #1E40AF; }
    .year-2024 { background: #D1FAE5; color: #065F46; }
    .year-2025 { background: #FEF3C7; color: #92400E; }
    .year-2026 { background: #F3E8FF; color: #6B21A8; }
    
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
        border: 1px solid #E2E8F0; border-radius: 12px; padding: 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    [data-testid="stMetric"]:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px); transition: all 0.2s ease;
    }
    [data-testid="stMetricLabel"] { font-weight: 600 !important; color: #475569 !important; }
    [data-testid="stMetricValue"] { font-size: 1.5rem !important; font-weight: 700 !important; color: #1E293B !important; }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# FUNGSI UTILITAS
# ============================================================================
def format_number(num):
    if pd.isna(num): return "0"
    return f"{num:,.0f}".replace(",", ".")

def format_pct(num):
    if pd.isna(num): return "0,00%"
    return f"{num:.2f}%".replace(".", ",")

def fmt_id(x):
    return f'{x:.2f}'.replace('.', ',')

def fmt_id_int(num):
    return f"{int(round(num)):,}".replace(",", ".")

def create_download_button(df, filename_prefix, key_prefix):
    """Download CSV saja (hemat memori)"""
    csv_data = df.to_csv(index=False, sep=';', decimal=',')
    st.download_button(
        label="📥 Download CSV", data=csv_data,
        file_name=f"{filename_prefix}.csv", mime="text/csv",
        key=f"{key_prefix}_csv"
    )

# ============================================================================
# FUNGSI LOAD & PROSES DATA (CACHED)
# ============================================================================
@st.cache_data(ttl=3600, max_entries=1)
def load_and_process(file_path):
    """Load + proses data dalam satu fungsi cached"""
    encodings = ['utf-8', 'cp1252', 'latin1', 'iso-8859-1']
    df = None
    for enc in encodings:
        try:
            df = pd.read_csv(file_path, encoding=enc)
            break
        except:
            continue
    if df is None:
        df = pd.read_csv(file_path, encoding='utf-8', errors='replace')
    
    # Bersihkan baris tidak valid
    for col in ['Kelurahan', 'Kecamatan', 'Puskesmas']:
        df = df[~df[col].astype(str).str.contains(r'\[', na=False)]
    
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
    
    if 'Tahun' in df.columns:
        df['Tahun'] = pd.to_numeric(df['Tahun'], errors='coerce').fillna(2025).astype(int)
    
    bulan_order = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                   'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    if 'Bulan' in df.columns:
        df['Bulan_Num'] = df['Bulan'].apply(lambda x: bulan_order.index(x) + 1 if x in bulan_order else 0)
    
    return df

def filter_data(df, tahun, bulan, kecamatan, puskesmas):
    """Filter tanpa copy (hemat memori)"""
    mask = pd.Series(True, index=df.index)
    if tahun: mask &= df['Tahun'].isin(tahun)
    if bulan: mask &= df['Bulan'].isin(bulan)
    if kecamatan: mask &= df['Kecamatan'].isin(kecamatan)
    if puskesmas: mask &= df['Puskesmas'].isin(puskesmas)
    return df[mask]

# ============================================================================
# SIDEBAR
# ============================================================================
def create_sidebar(df):
    st.sidebar.markdown('<div style="text-align:center;padding:1rem 0;"><h2 style="color:#0C4A6E;margin:0;">🔍 Filter Data</h2></div>', unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    tahun_list = sorted(df['Tahun'].unique(), reverse=True)
    st.sidebar.markdown("### 📅 Periode")
    
    year_mode = st.sidebar.radio("Mode Tahun", ["Satu Tahun", "Bandingkan Tahun", "Semua Tahun"], horizontal=True)
    
    if year_mode == "Satu Tahun":
        selected_tahun = [st.sidebar.selectbox("Pilih Tahun", options=tahun_list)]
    elif year_mode == "Bandingkan Tahun":
        selected_tahun = st.sidebar.multiselect("Pilih Tahun", options=tahun_list, default=tahun_list[:min(2, len(tahun_list))])
    else:
        selected_tahun = tahun_list
    
    bulan_order = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                   'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    bulan_available = [b for b in bulan_order if b in df['Bulan'].unique()]
    selected_bulan = st.sidebar.multiselect("🗓️ Bulan", options=bulan_available, default=bulan_available)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🏘️ Wilayah")
    
    kecamatan_list = sorted(df['Kecamatan'].dropna().unique())
    selected_kecamatan = st.sidebar.multiselect("Kecamatan", options=kecamatan_list, default=kecamatan_list)
    
    if selected_kecamatan:
        puskesmas_list = sorted(df[df['Kecamatan'].isin(selected_kecamatan)]['Puskesmas'].dropna().unique())
    else:
        puskesmas_list = sorted(df['Puskesmas'].dropna().unique())
    selected_puskesmas = st.sidebar.multiselect("Puskesmas", options=puskesmas_list, default=puskesmas_list)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Info Data")
    st.sidebar.info(f"**Tahun:** {', '.join(map(str, sorted(tahun_list)))}\n\n**Record:** {len(df):,}\n\n**Kelurahan:** {df['Kelurahan'].nunique()}")
    
    if st.sidebar.button("🔄 Reset Filter", use_container_width=True):
        st.rerun()
    
    return selected_tahun, selected_bulan, selected_kecamatan, selected_puskesmas, year_mode

# ============================================================================
# GAUGE CHART
# ============================================================================
def create_gauge_chart(value, title, max_val=30, threshold_warning=14, threshold_danger=20):
    if pd.isna(value): value = 0
    if value < threshold_warning: color, status = "#16A34A", "Baik"
    elif value < threshold_danger: color, status = "#F59E0B", "Sedang"
    else: color, status = "#DC2626", "Tinggi"
    
    value_formatted = f"{value:.2f}".replace(".", ",") + "%"
    
    fig = go.Figure(go.Indicator(
        mode="gauge", value=value,
        title={'text': f"{title}<br><span style='font-size:12px;color:{color}'>{status}</span>", 'font': {'size': 14, 'color': '#64748B'}},
        gauge={
            'axis': {'range': [0, max_val], 'tickwidth': 1},
            'bar': {'color': color, 'thickness': 0.75},
            'bgcolor': '#F1F5F9', 'borderwidth': 0,
            'steps': [
                {'range': [0, threshold_warning], 'color': '#DCFCE7'},
                {'range': [threshold_warning, threshold_danger], 'color': '#FEF3C7'},
                {'range': [threshold_danger, max_val], 'color': '#FEE2E2'}
            ]
        }
    ))
    fig.add_annotation(x=0.5, y=0.25, text=value_formatted, font=dict(size=32, color='#1E293B'), showarrow=False, xref="paper", yref="paper")
    fig.update_layout(height=180, margin=dict(l=20, r=20, t=50, b=10), paper_bgcolor='rgba(0,0,0,0)')
    return fig

# ============================================================================
# TAB OVERVIEW
# ============================================================================
def render_overview(df, year_mode):
    if 'Bulan' in df.columns:
        monthly_agg = df.groupby(['Tahun', 'Bulan']).agg({
            'Balita_Bulan_Ini': 'sum', 'Balita_Ditimbang': 'sum',
            'Jml_Balita_Stunting': 'sum', 'Jml_Balita_Wasting': 'sum',
            'Jml_Balita_Overweight': 'sum', 'Jml_Balita_Underweight': 'sum'
        }).reset_index()
        
        avg_sasaran = int(round(monthly_agg['Balita_Bulan_Ini'].mean()))
        avg_ditimbang = int(round(monthly_agg['Balita_Ditimbang'].mean()))
        avg_stunting = int(round(monthly_agg['Jml_Balita_Stunting'].mean()))
        avg_wasting = int(round(monthly_agg['Jml_Balita_Wasting'].mean()))
        avg_overweight = int(round(monthly_agg['Jml_Balita_Overweight'].mean()))
        avg_underweight = int(round(monthly_agg['Jml_Balita_Underweight'].mean()))
        jumlah_bulan = len(monthly_agg)
        del monthly_agg
    else:
        avg_sasaran = int(df['Balita_Bulan_Ini'].sum())
        avg_ditimbang = int(df['Balita_Ditimbang'].sum())
        avg_stunting = int(df['Jml_Balita_Stunting'].sum())
        avg_wasting = int(df['Jml_Balita_Wasting'].sum())
        avg_overweight = int(df['Jml_Balita_Overweight'].sum())
        avg_underweight = int(df['Jml_Balita_Underweight'].sum())
        jumlah_bulan = 1
    
    pct_stunting = round((avg_stunting / avg_ditimbang) * 100, 2) if avg_ditimbang > 0 else 0
    pct_wasting = round((avg_wasting / avg_ditimbang) * 100, 2) if avg_ditimbang > 0 else 0
    pct_overweight = round((avg_overweight / avg_ditimbang) * 100, 2) if avg_ditimbang > 0 else 0
    pct_underweight = round((avg_underweight / avg_ditimbang) * 100, 2) if avg_ditimbang > 0 else 0
    pct_cakupan = round((avg_ditimbang / avg_sasaran) * 100, 2) if avg_sasaran > 0 else 0
    
    tahun_list = sorted(df['Tahun'].unique())
    badges = ''.join([f'<span class="year-badge year-{t}">{t}</span>' for t in tahun_list])
    
    st.markdown(f"""
    <div class="info-card">
        <strong>📅 Periode:</strong> {badges} &nbsp;|&nbsp;
        <strong>📊 Kelurahan:</strong> {df['Kelurahan'].nunique()} &nbsp;|&nbsp;
        <strong>🏥 Puskesmas:</strong> {df['Puskesmas'].nunique()} &nbsp;|&nbsp;
        <strong>📆 Data:</strong> Rata-rata {jumlah_bulan} bulan
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">📊 Indikator Utama (Rata-rata Bulanan)</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("👶 Balita Ditimbang", format_number(avg_ditimbang))
        st.markdown(f'<p style="color:#2563EB;font-size:0.85rem;margin-top:-10px;">Rata-rata per Bulan</p>', unsafe_allow_html=True)
    with col2:
        st.metric("📏 Stunting", format_pct(pct_stunting))
        st.markdown(f'<p style="color:#2563EB;font-size:0.85rem;margin-top:-10px;"><strong>{format_number(avg_stunting)}</strong> balita/bulan</p>', unsafe_allow_html=True)
    with col3:
        st.metric("⚖️ Wasting", format_pct(pct_wasting))
        st.markdown(f'<p style="color:#2563EB;font-size:0.85rem;margin-top:-10px;"><strong>{format_number(avg_wasting)}</strong> balita/bulan</p>', unsafe_allow_html=True)
    with col4:
        st.metric("📈 Overweight", format_pct(pct_overweight))
        st.markdown(f'<p style="color:#2563EB;font-size:0.85rem;margin-top:-10px;"><strong>{format_number(avg_overweight)}</strong> balita/bulan</p>', unsafe_allow_html=True)
    with col5:
        st.metric("⬇️ Underweight", format_pct(pct_underweight))
        st.markdown(f'<p style="color:#2563EB;font-size:0.85rem;margin-top:-10px;"><strong>{format_number(avg_underweight)}</strong> balita/bulan</p>', unsafe_allow_html=True)
    with col6:
        st.metric("📋 % D/S", format_pct(pct_cakupan))
        st.markdown(f'<p style="color:#2563EB;font-size:0.85rem;margin-top:-10px;">Cakupan Penimbangan</p>', unsafe_allow_html=True)
    
    # Catatan Rumus
    st.markdown(f"""
    <div style="background-color:#F0FDF4;border:1px solid #86EFAC;border-radius:8px;padding:12px;margin-top:10px;font-size:0.85rem;">
        <strong>📝 Catatan Rumus Perhitungan:</strong><br><br>
        <table style="width:100%;border-collapse:collapse;font-size:0.85rem;">
            <tr style="border-bottom:1px solid #86EFAC;"><td style="padding:4px 8px;width:20%;"><strong>Stunting</strong></td><td style="padding:4px 8px;">= (Balita Stunting / Balita Ditimbang) × 100%</td><td style="padding:4px 8px;">= ({format_number(avg_stunting)} / {format_number(avg_ditimbang)}) × 100%</td><td style="padding:4px 8px;text-align:right;"><strong>{format_pct(pct_stunting)}</strong></td></tr>
            <tr style="border-bottom:1px solid #86EFAC;"><td style="padding:4px 8px;"><strong>Wasting</strong></td><td style="padding:4px 8px;">= (Balita Wasting / Balita Ditimbang) × 100%</td><td style="padding:4px 8px;">= ({format_number(avg_wasting)} / {format_number(avg_ditimbang)}) × 100%</td><td style="padding:4px 8px;text-align:right;"><strong>{format_pct(pct_wasting)}</strong></td></tr>
            <tr style="border-bottom:1px solid #86EFAC;"><td style="padding:4px 8px;"><strong>Overweight</strong></td><td style="padding:4px 8px;">= (Balita Overweight / Balita Ditimbang) × 100%</td><td style="padding:4px 8px;">= ({format_number(avg_overweight)} / {format_number(avg_ditimbang)}) × 100%</td><td style="padding:4px 8px;text-align:right;"><strong>{format_pct(pct_overweight)}</strong></td></tr>
            <tr style="border-bottom:1px solid #86EFAC;"><td style="padding:4px 8px;"><strong>Underweight</strong></td><td style="padding:4px 8px;">= (Balita Underweight / Balita Ditimbang) × 100%</td><td style="padding:4px 8px;">= ({format_number(avg_underweight)} / {format_number(avg_ditimbang)}) × 100%</td><td style="padding:4px 8px;text-align:right;"><strong>{format_pct(pct_underweight)}</strong></td></tr>
            <tr><td style="padding:4px 8px;"><strong>% D/S</strong></td><td style="padding:4px 8px;">= (Balita Ditimbang / Sasaran Balita) × 100%</td><td style="padding:4px 8px;">= ({format_number(avg_ditimbang)} / {format_number(avg_sasaran)}) × 100%</td><td style="padding:4px 8px;text-align:right;"><strong>{format_pct(pct_cakupan)}</strong></td></tr>
        </table>
    </div>
    """, unsafe_allow_html=True)
    
    # Gauge Charts
    st.markdown('<div class="section-header">🎯 Status Terhadap Target</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        fig = create_gauge_chart(pct_stunting, "Stunting", 35, 14, 20)
        st.plotly_chart(fig, use_container_width=True); del fig
    with col2:
        fig = create_gauge_chart(pct_wasting, "Wasting", 15, 5, 10)
        st.plotly_chart(fig, use_container_width=True); del fig
    with col3:
        fig = create_gauge_chart(pct_overweight, "Overweight", 15, 5, 10)
        st.plotly_chart(fig, use_container_width=True); del fig
    with col4:
        fig = create_gauge_chart(pct_underweight, "Underweight", 25, 10, 15)
        st.plotly_chart(fig, use_container_width=True); del fig
    
    # Perbandingan Tahun
    if len(df['Tahun'].unique()) > 1:
        st.markdown('<div class="section-header">📈 Perbandingan Antar Tahun</div>', unsafe_allow_html=True)
        
        yearly_data = df.groupby('Tahun').agg({
            'Balita_Ditimbang': 'sum', 'Jml_Balita_Stunting': 'sum',
            'Jml_Balita_Wasting': 'sum', 'Jml_Balita_Overweight': 'sum', 'Jml_Balita_Underweight': 'sum'
        }).reset_index()
        
        for ind in ['Stunting', 'Wasting', 'Overweight', 'Underweight']:
            yearly_data[f'Pct_{ind}'] = (yearly_data[f'Jml_Balita_{ind}'] / yearly_data['Balita_Ditimbang'] * 100).round(2)
        
        fig = go.Figure()
        colors = {'Stunting': '#DC2626', 'Wasting': '#F59E0B', 'Overweight': '#0891B2', 'Underweight': '#7C3AED'}
        for ind, clr in colors.items():
            fig.add_trace(go.Bar(name=ind, x=yearly_data['Tahun'].astype(str), y=yearly_data[f'Pct_{ind}'],
                                 marker_color=clr, text=yearly_data[f'Pct_{ind}'].apply(lambda x: f'{x:.2f}%'.replace('.',',')),
                                 textposition='outside'))
        fig.add_hline(y=14, line_dash="dash", line_color="green", annotation_text="Target Stunting 14%")
        fig.update_layout(title='📊 Perbandingan Prevalensi Antar Tahun', barmode='group', height=400,
                          xaxis_title="Tahun", yaxis_title="Prevalensi (%)",
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        del fig, yearly_data
    
    gc.collect()

# ============================================================================
# TAB TREND
# ============================================================================
def render_trend(df):
    st.markdown('<div class="section-header">📈 Trend Bulanan</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col2:
        indicator = st.selectbox("Pilih Indikator", ["Stunting", "Wasting", "Overweight", "Underweight"], key="trend_ind")
    
    indicator_col = f'Pct_{indicator}'
    
    # Aggregasi trend
    trend_data = df.groupby(['Tahun', 'Bulan', 'Bulan_Num']).agg({
        'Balita_Bulan_Ini': 'sum', 'Balita_Ditimbang': 'sum', 'Jml_Balita_Stunting': 'sum',
        'Jml_Balita_Wasting': 'sum', 'Jml_Balita_Overweight': 'sum', 'Jml_Balita_Underweight': 'sum'
    }).reset_index().sort_values(['Tahun', 'Bulan_Num'])
    
    for ind in ['Stunting', 'Wasting', 'Overweight', 'Underweight']:
        trend_data[f'Pct_{ind}'] = (trend_data[f'Jml_Balita_{ind}'] / trend_data['Balita_Ditimbang'] * 100).round(1)
    
    # Line chart
    colors = {2023: '#3B82F6', 2024: '#10B981', 2025: '#EF4444', 2026: '#8B5CF6', 2027: '#F59E0B'}
    fig = go.Figure()
    for tahun in sorted(trend_data['Tahun'].unique()):
        dt = trend_data[trend_data['Tahun'] == tahun]
        fig.add_trace(go.Scatter(x=dt['Bulan'], y=dt[indicator_col], mode='lines+markers',
                                 name=str(tahun), line=dict(color=colors.get(tahun, '#64748B'), width=3),
                                 marker=dict(size=8)))
    target_val = 14 if 'Stunting' in indicator_col else 5
    fig.add_hline(y=target_val, line_dash="dash", line_color="green", annotation_text=f"Target {target_val}%")
    fig.update_layout(title=f'📈 Trend Prevalensi {indicator} per Bulan', height=400,
                      xaxis_title="Bulan", yaxis_title="Prevalensi (%)",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                      hovermode='x unified', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    
    with col1:
        st.plotly_chart(fig, use_container_width=True)
    del fig
    
    # Area chart
    st.markdown('<div class="section-header">📊 Jumlah Kasus per Bulan</div>', unsafe_allow_html=True)
    fig = px.area(trend_data, x='Bulan', y=f'Jml_Balita_{indicator}', color='Tahun',
                  title=f'📊 Jumlah Kasus {indicator} per Bulan', color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(height=350, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)
    del fig
    
    # Tabel
    st.markdown(f'<div class="section-header">📋 Tabel Data {indicator} Bulanan</div>', unsafe_allow_html=True)
    
    tbl = trend_data[['Tahun', 'Bulan', 'Balita_Bulan_Ini', 'Balita_Ditimbang', f'Jml_Balita_{indicator}', indicator_col]].copy()
    tbl['Balita_Bulan_Ini'] = tbl['Balita_Bulan_Ini'].apply(fmt_id_int)
    tbl['Balita_Ditimbang'] = tbl['Balita_Ditimbang'].apply(fmt_id_int)
    tbl[f'Jml_Balita_{indicator}'] = tbl[f'Jml_Balita_{indicator}'].apply(fmt_id_int)
    tbl[indicator_col] = tbl[indicator_col].apply(fmt_id)
    tbl.columns = ['Tahun', 'Bulan', 'Sasaran Balita', 'Balita Ditimbang', f'Jml {indicator}', 'Prevalensi (%)']
    st.dataframe(tbl, use_container_width=True, hide_index=True)
    create_download_button(tbl, f"data_trend_{indicator.lower()}", f"trend_{indicator.lower()}")
    
    del trend_data, tbl
    gc.collect()

# ============================================================================
# TAB DISTRIBUSI
# ============================================================================
def render_distribution(df):
    st.markdown('<div class="section-header">🗺️ Distribusi per Wilayah (Rata-rata Bulanan)</div>', unsafe_allow_html=True)
    
    col_filter, _ = st.columns([1, 3])
    with col_filter:
        indicator = st.selectbox("Pilih Indikator", ["Stunting", "Wasting", "Overweight", "Underweight"], key="dist_indicator")
    
    target_config = {"Stunting": 14, "Wasting": 5, "Overweight": 5, "Underweight": 10}
    target_val = target_config[indicator]
    
    # Rata-rata bulanan per Puskesmas
    puskesmas_avg = df.groupby(['Tahun', 'Bulan', 'Puskesmas']).agg({
        'Balita_Ditimbang': 'sum', f'Jml_Balita_{indicator}': 'sum'
    }).reset_index().groupby('Puskesmas').agg({
        'Balita_Ditimbang': 'mean', f'Jml_Balita_{indicator}': 'mean'
    }).reset_index()
    puskesmas_avg[f'Pct_{indicator}'] = (puskesmas_avg[f'Jml_Balita_{indicator}'] / puskesmas_avg['Balita_Ditimbang'] * 100).round(2)
    puskesmas_avg = puskesmas_avg.sort_values(f'Pct_{indicator}', ascending=True)
    
    # Rata-rata bulanan per Kelurahan
    kelurahan_avg = df.groupby(['Tahun', 'Bulan', 'Kecamatan', 'Kelurahan']).agg({
        'Balita_Ditimbang': 'sum', f'Jml_Balita_{indicator}': 'sum', f'Pct_Balita_{indicator}': 'mean'
    }).reset_index().groupby(['Kecamatan', 'Kelurahan']).agg({
        'Balita_Ditimbang': 'mean', f'Jml_Balita_{indicator}': 'mean', f'Pct_Balita_{indicator}': 'mean'
    }).reset_index()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(puskesmas_avg, x=f'Pct_{indicator}', y='Puskesmas', orientation='h',
                     title=f'📊 Prevalensi {indicator} per Puskesmas',
                     color=f'Pct_{indicator}', color_continuous_scale=['#16A34A', '#F59E0B', '#DC2626'],
                     text=f'Pct_{indicator}')
        fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig.add_vline(x=target_val, line_dash="dash", line_color="green", annotation_text=f"Target {target_val}%")
        max_val = puskesmas_avg[f'Pct_{indicator}'].max()
        fig.update_layout(height=350, showlegend=False, margin=dict(l=10, r=80, t=40, b=40), xaxis=dict(range=[0, max_val * 1.3]))
        st.plotly_chart(fig, use_container_width=True); del fig
    
    with col2:
        kelurahan_sorted = kelurahan_avg.sort_values(f'Pct_Balita_{indicator}', ascending=True)
        fig = px.bar(kelurahan_sorted, x=f'Pct_Balita_{indicator}', y='Kelurahan', orientation='h',
                     title=f'📊 Prevalensi {indicator} per Kelurahan',
                     color=f'Pct_Balita_{indicator}', color_continuous_scale=['#16A34A', '#F59E0B', '#DC2626'],
                     text=f'Pct_Balita_{indicator}')
        fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig.add_vline(x=target_val, line_dash="dash", line_color="green", annotation_text=f"Target {target_val}%")
        max_val_kel = kelurahan_sorted[f'Pct_Balita_{indicator}'].max()
        fig.update_layout(height=450, showlegend=False, margin=dict(l=10, r=80, t=40, b=40), xaxis=dict(range=[0, max_val_kel * 1.3]))
        st.plotly_chart(fig, use_container_width=True); del fig
    
    # Tabel
    st.markdown(f'<div class="section-header">📋 Tabel Data {indicator}</div>', unsafe_allow_html=True)
    col_tbl1, col_tbl2 = st.columns(2)
    
    with col_tbl1:
        st.markdown("**Data per Puskesmas**")
        tbl_p = puskesmas_avg[['Puskesmas', 'Balita_Ditimbang', f'Jml_Balita_{indicator}', f'Pct_{indicator}']].sort_values(f'Pct_{indicator}', ascending=False).copy()
        tbl_p['Balita_Ditimbang'] = tbl_p['Balita_Ditimbang'].apply(fmt_id_int)
        tbl_p[f'Jml_Balita_{indicator}'] = tbl_p[f'Jml_Balita_{indicator}'].apply(fmt_id_int)
        tbl_p[f'Pct_{indicator}'] = tbl_p[f'Pct_{indicator}'].apply(fmt_id)
        tbl_p.columns = ['Puskesmas', 'Balita Ditimbang', f'Jml {indicator}', 'Prevalensi (%)']
        st.dataframe(tbl_p, use_container_width=True, hide_index=True)
        create_download_button(tbl_p, f"data_{indicator.lower()}_puskesmas", f"puskesmas_{indicator.lower()}")
    
    with col_tbl2:
        st.markdown("**Data per Kelurahan**")
        tbl_k = kelurahan_avg[['Kelurahan', 'Balita_Ditimbang', f'Jml_Balita_{indicator}', f'Pct_Balita_{indicator}']].sort_values(f'Pct_Balita_{indicator}', ascending=False).copy()
        tbl_k['Balita_Ditimbang'] = tbl_k['Balita_Ditimbang'].apply(fmt_id_int)
        tbl_k[f'Jml_Balita_{indicator}'] = tbl_k[f'Jml_Balita_{indicator}'].apply(fmt_id_int)
        tbl_k[f'Pct_Balita_{indicator}'] = tbl_k[f'Pct_Balita_{indicator}'].apply(fmt_id)
        tbl_k.columns = ['Kelurahan', 'Balita Ditimbang', f'Jml {indicator}', 'Prevalensi (%)']
        st.dataframe(tbl_k, use_container_width=True, hide_index=True)
        create_download_button(tbl_k, f"data_{indicator.lower()}_kelurahan", f"kelurahan_{indicator.lower()}")
    
    # Scatter plot
    st.markdown('<div class="section-header">🔍 Analisis Korelasi</div>', unsafe_allow_html=True)
    
    scatter_avg = df.groupby(['Tahun', 'Bulan', 'Kecamatan', 'Kelurahan']).agg({
        'Balita_Ditimbang': 'sum', 'Jml_Balita_Stunting': 'sum', 'Jml_Balita_Wasting': 'sum'
    }).reset_index().groupby(['Kecamatan', 'Kelurahan']).agg({
        'Balita_Ditimbang': 'mean', 'Jml_Balita_Stunting': 'mean', 'Jml_Balita_Wasting': 'mean'
    }).reset_index()
    scatter_avg['Pct_Stunting'] = (scatter_avg['Jml_Balita_Stunting'] / scatter_avg['Balita_Ditimbang'] * 100).round(2)
    scatter_avg['Pct_Wasting'] = (scatter_avg['Jml_Balita_Wasting'] / scatter_avg['Balita_Ditimbang'] * 100).round(2)
    
    color_kec = {'BONTANG UTARA': '#2563EB', 'BONTANG BARAT': '#16A34A', 'BONTANG SELATAN': '#DC2626'}
    fig = px.scatter(scatter_avg, x='Pct_Stunting', y='Pct_Wasting', size='Balita_Ditimbang',
                     color='Kecamatan', hover_name='Kelurahan', color_discrete_map=color_kec,
                     title='📊 Korelasi Stunting vs Wasting per Kelurahan',
                     labels={'Pct_Stunting': 'Stunting (%)', 'Pct_Wasting': 'Wasting (%)'})
    fig.add_hline(y=5, line_dash="dash", line_color="orange", opacity=0.5)
    fig.add_vline(x=14, line_dash="dash", line_color="red", opacity=0.5)
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)
    
    del fig, puskesmas_avg, kelurahan_avg, scatter_avg, tbl_p, tbl_k
    gc.collect()

# ============================================================================
# TAB PERBANDINGAN
# ============================================================================
def render_comparison(df):
    st.markdown('<div class="section-header">⚖️ Perbandingan Antar Wilayah (Rata-rata Bulanan)</div>', unsafe_allow_html=True)
    
    level = st.radio("Pilih Level Perbandingan", ["Kelurahan", "Kecamatan", "Puskesmas"], horizontal=True)
    wilayah_col = level
    
    agg_cols = {'Balita_Bulan_Ini': 'sum', 'Balita_Ditimbang': 'sum',
                'Jml_Balita_Stunting': 'sum', 'Jml_Balita_Wasting': 'sum',
                'Jml_Balita_Overweight': 'sum', 'Jml_Balita_Underweight': 'sum'}
    
    monthly = df.groupby(['Tahun', 'Bulan', wilayah_col]).agg(agg_cols).reset_index()
    df_agg = monthly.groupby(wilayah_col).agg({k: 'mean' for k in agg_cols}).reset_index()
    del monthly
    
    for ind in ['Stunting', 'Wasting', 'Overweight', 'Underweight']:
        df_agg[f'Pct_{ind}'] = (df_agg[f'Jml_Balita_{ind}'] / df_agg['Balita_Ditimbang'] * 100).round(2)
    df_agg['Pct_DS'] = (df_agg['Balita_Ditimbang'] / df_agg['Balita_Bulan_Ini'] * 100).round(2)
    
    wilayah_list = sorted(df_agg[wilayah_col].unique())
    
    col1, col2 = st.columns(2)
    with col1:
        wilayah1 = st.selectbox(f"Pilih {level} 1", options=wilayah_list, key='w1')
    with col2:
        wilayah2 = st.selectbox(f"Pilih {level} 2", options=[k for k in wilayah_list if k != wilayah1], key='w2')
    
    data1 = df_agg[df_agg[wilayah_col] == wilayah1].iloc[0]
    data2 = df_agg[df_agg[wilayah_col] == wilayah2].iloc[0]
    
    categories = ['Stunting', 'Wasting', 'Overweight', 'Underweight', '% D/S']
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[data1['Pct_Stunting'], data1['Pct_Wasting'], data1['Pct_Overweight'], data1['Pct_Underweight'], data1['Pct_DS']],
        theta=categories, fill='toself', name=wilayah1, line_color='#2563EB', fillcolor='rgba(37,99,235,0.25)'))
    fig.add_trace(go.Scatterpolar(
        r=[data2['Pct_Stunting'], data2['Pct_Wasting'], data2['Pct_Overweight'], data2['Pct_Underweight'], data2['Pct_DS']],
        theta=categories, fill='toself', name=wilayah2, line_color='#16A34A', fillcolor='rgba(22,163,74,0.25)'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                      title=f'📊 Perbandingan {wilayah1} vs {wilayah2}', height=450)
    st.plotly_chart(fig, use_container_width=True)
    del fig
    
    # Tabel perbandingan
    st.markdown(f'<div class="section-header">📋 Detail Perbandingan {level}</div>', unsafe_allow_html=True)
    
    inds = ['Stunting', 'Wasting', 'Overweight', 'Underweight']
    comparison_data = {
        'Indikator': inds + ['% D/S (Cakupan)'],
        wilayah1: [format_pct(data1[f'Pct_{i}']) for i in inds] + [format_pct(data1['Pct_DS'])],
        wilayah2: [format_pct(data2[f'Pct_{i}']) for i in inds] + [format_pct(data2['Pct_DS'])],
        'Selisih': [f"{(data1[f'Pct_{i}'] - data2[f'Pct_{i}']):+.2f}%".replace('.',',') for i in inds] + [f"{(data1['Pct_DS'] - data2['Pct_DS']):+.2f}%".replace('.',',')]
    }
    
    df_comp = pd.DataFrame(comparison_data)
    st.dataframe(df_comp, use_container_width=True, hide_index=True)
    create_download_button(df_comp, f"perbandingan_{wilayah1}_vs_{wilayah2}", f"comp_{level}")
    
    del df_agg, df_comp
    gc.collect()

# ============================================================================
# MAIN APP - Menggunakan radio button agar hanya 1 halaman di-render
# ============================================================================
def main():
    st.markdown("""
    <div class="dashboard-header">
        <h1>🏥 Dashboard Status Gizi Balita</h1>
        <p>Dinas Kesehatan Kota Bontang - Provinsi Kalimantan Timur</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        df = load_and_process('Database_Gizi_Clean.csv')
    except FileNotFoundError:
        st.error("⚠️ File `Database_Gizi_Clean.csv` tidak ditemukan.")
        st.stop()
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.stop()
    
    selected_tahun, selected_bulan, selected_kecamatan, selected_puskesmas, year_mode = create_sidebar(df)
    df_filtered = filter_data(df, selected_tahun, selected_bulan, selected_kecamatan, selected_puskesmas)
    
    if len(df_filtered) == 0:
        st.warning("⚠️ Tidak ada data yang sesuai dengan filter.")
        st.stop()
    
    # KUNCI OPTIMASI: gunakan radio button, bukan tabs
    # Dengan radio, hanya halaman yang dipilih yang di-render
    # Dengan tabs, SEMUA halaman di-render setiap kali ada interaksi
    halaman = st.radio(
        "Pilih Halaman",
        ["📊 Overview", "📈 Trend", "🗺️ Distribusi", "⚖️ Perbandingan"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    if halaman == "📊 Overview":
        render_overview(df_filtered, year_mode)
    elif halaman == "📈 Trend":
        render_trend(df_filtered)
    elif halaman == "🗺️ Distribusi":
        render_distribution(df_filtered)
    elif halaman == "⚖️ Perbandingan":
        render_comparison(df_filtered)
    
    st.markdown("---")
    st.markdown('<div style="text-align:center;color:#64748B;font-size:1rem;">📊 Dashboard Status Gizi Balita - Dinas Kesehatan Kota Bontang | © 2025</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
