import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ==============================================================================
# STREAMLIT SAYFA YAPILANDIRMASI
# ==============================================================================
st.set_page_config(
    page_title="BIST Ichimoku v29 Canlı Taraması",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📈 BIST Ichimoku Kinko Hyo (v29) Canlı Tarama & Sinyal Motoru")
st.markdown("""
**Goichi Hosoda** felsefesi ve v29 gelişmiş strateji kuralları (Madde 1 Ana Alım, Madde 2a Aşırı Satış Tepki Alımı, Madde 2b Kısmi Alım, Madde 3 Engel Filtreleri ve Dinamik Çıkış Yönetimi) ile **Borsa İstanbul** hisse senedi ve BYF canlı tarayıcısı.
""")

# ==============================================================================
# BIST SEMBOL LİSTESİ
# ==============================================================================
DEFAULT_SYMBOLS = [
    "THYAO.IS", "GARAN.IS", "EREGL.IS", "AKBNK.IS", "ISCTR.IS",
    "SAHOL.IS", "KCHOL.IS", "BIMAS.IS", "ASELS.IS", "TUPRS.IS",
    "SISE.IS", "EKGYO.IS", "YKBNK.IS", "ENKAI.IS", "DOHOL.IS",
    "PETKM.IS", "TOASO.IS", "FROTO.IS", "TTKOM.IS", "TCELL.IS",
    "HEKTS.IS", "GUBRF.IS", "SASA.IS", "ALARK.IS", "ODAS.IS",
    "KOZAL.IS", "KOZAA.IS", "IPEKE.IS", "VESTL.IS", "VESBE.IS",
    "ALVES.IS", "CAN.IS", "TEHOL.IS", "ZBYF.IS"
]

# ==============================================================================
# ICHIMOKU V29 HESAPLAMA MOTORU
# ==============================================================================
def calculate_ichimoku_v29(df, tenkan_len=9, kijun_len=26, senkou_b_len=52, displacement=26):
    if len(df) < senkou_b_len + displacement:
        return None

    high = df['High']
    low = df['Low']
    close = df['Close']
    open_p = df['Open']

    # Donchian Orta Noktaları
    tenkan = (high.rolling(window=tenkan_len).max() + low.rolling(window=tenkan_len).min()) / 2
    kijun = (high.rolling(window=kijun_len).max() + low.rolling(window=kijun_len).min()) / 2
    senkou_a = (tenkan + kijun) / 2
    senkou_b = (high.rolling(window=senkou_b_len).max() + low.rolling(window=senkou_b_len).min()) / 2

    # Tenkan Sapması
    dev = ((close - tenkan) / tenkan) * 100.0

    # DataFrame'e Ekleme
    res = df.copy()
    res['tenkan'] = tenkan
    res['kijun'] = kijun
    res['senkou_a'] = senkou_a
    res['senkou_b'] = senkou_b
    res['dev'] = dev

    # Senkou Span A ve B (Görsel Offset: 25 bar ileri)
    res['senkou_a_future'] = senkou_a.shift(displacement - 1)
    res['senkou_b_future'] = senkou_b.shift(displacement - 1)

    # Güncel bar hizasındaki bulut değerleri (25 bar gerideki Senkou'lar)
    res['senkou_a_curr'] = senkou_a.shift(displacement - 1)
    res['senkou_b_curr'] = senkou_b.shift(displacement - 1)

    # Chikou Span Onayı (25 bar önceki kapanış)
    res['close_prev_25'] = close.shift(displacement - 1)
    res['chikou_above'] = close > res['close_prev_25']

    # Madde 1 Temel Şartları
    res['cond_1a'] = (close > res['senkou_a_curr']) & (close > res['senkou_b_curr'])
    res['cond_1b'] = res['chikou_above']
    res['cond_1c'] = senkou_a > senkou_b
    res['cond_1d'] = tenkan > kijun
    res['base_rule_1'] = res['cond_1a'] & res['cond_1b'] & res['cond_1c'] & res['cond_1d']

    # Madde 3 Filtreleri
    cloud_thickness_pct = (np.abs(senkou_a - senkou_b) / close) * 100.0
    res['filter_thin_cloud'] = cloud_thickness_pct < 0.3

    is_flat_kijun = (kijun.rolling(5).max() == kijun.rolling(5).min())
    is_flat_senkou_b = (senkou_b.rolling(5).max() == senkou_b.rolling(5).min())
    res['filter_flat_line'] = is_flat_kijun | is_flat_senkou_b

    res['filter_overbought'] = dev >= 20.0  # Aşırı Alım Bölgesi Alım Engeli

    dist_to_tenkan_pct = np.abs((close - tenkan) / tenkan) * 100.0
    is_near_tenkan = dist_to_tenkan_pct <= 10.0
    touched_tk = (low <= tenkan) | (low <= kijun)
    is_bounce = (close > open_p) | (close > close.shift(1))
    res['tenkan_proximity'] = is_near_tenkan | (touched_tk & is_bounce)

    # Genel Alım Engeli
    res['no_buy_filter'] = res['filter_thin_cloud'] | res['filter_overbought']

    # Sinyal Tespiti (Son Bar)
    n = len(res) - 1
    last_row = res.iloc[n]
    
    signal = "NÖTR"
    signal_color = "gray"
    reason = "Şartlar oluşmadı"

    if last_row['base_rule_1'] and not last_row['no_buy_filter']:
        signal = "AL (Madde 1 - Ana Alım)"
        signal_color = "green"
        reason = "4/4 Tam Boğa Hizalanması + Filtre Onayı"
    elif last_row['dev'] <= -20.0:
        signal = "AŞIRI SATIŞ UYARISI"
        signal_color = "orange"
        reason = "Tenkan-sen Sapması <= -%20 (Tepki Alımı Kurulumu Takipte)"
    elif last_row['filter_overbought']:
        signal = "AŞIRI ALIM UYARISI"
        signal_color = "red"
        reason = "Tenkan-sen Sapması >= %20 (Kar Alım Çıkışı Takip Edilmeli)"

    return {
        'data': res,
        'last_close': last_row['Close'],
        'last_tenkan': last_row['tenkan'],
        'last_kijun': last_row['kijun'],
        'dev_pct': last_row['dev'],
        'signal': signal,
        'signal_color': signal_color,
        'reason': reason
    }

# ==============================================================================
# YAN MENÜ (SIDEBAR) & AYARLAR
# ==============================================================================
st.sidebar.header("⚙️ Tarama Parametreleri")

tenkan_p = st.sidebar.number_input("Tenkan-sen Periyodu", value=9, min_value=1)
kijun_p = st.sidebar.number_input("Kijun-sen Periyodu", value=26, min_value=1)
senkou_b_p = st.sidebar.number_input("Senkou Span B Periyodu", value=52, min_value=1)

custom_symbols_text = st.sidebar.text_area(
    "Özel Sembol Ekle (Virgülle ayırarak .IS uzantılı yazın):",
    value=""
)

if custom_symbols_text.strip():
    user_syms = [s.strip().upper() for s in custom_symbols_text.split(",") if s.strip()]
    active_symbols = list(set(DEFAULT_SYMBOLS + user_syms))
else:
    active_symbols = DEFAULT_SYMBOLS

# ==============================================================================
# CANLI TARAMA MOTORU
# ==============================================================================
st.subheader("🔍 BIST Canlı Tarama Sonuçları")

if st.button("🚀 Taramayı Başlat", type="primary"):
    results = []
    progress_bar = st.progress(0)
    
    for idx, sym in enumerate(active_symbols):
        try:
            ticker = yf.Ticker(sym)
            df = ticker.history(period="1y")
            if not df.empty and len(df) >= 80:
                res = calculate_ichimoku_v29(df, tenkan_p, kijun_p, senkou_b_p)
                if res:
                    results.append({
                        "Hisse / Sembol": sym.replace(".IS", ""),
                        "Son Fiyat (TL)": round(res['last_close'], 2),
                        "Tenkan-sen": round(res['last_tenkan'], 2),
                        "Kijun-sen": round(res['last_kijun'], 2),
                        "Tenkan Sapması (%)": round(res['dev_pct'], 2),
                        "Sinyal Durumu": res['signal'],
                        "Açıklama": res['reason']
                    })
        except Exception as e:
            pass
        progress_bar.progress((idx + 1) / len(active_symbols))

    if results:
        res_df = pd.DataFrame(results)
        st.session_state['res_df'] = res_df
        st.success(f"Tarama Tamamlandı! Toplam {len(results)} sembol analiz edildi.")

if 'res_df' in st.session_state:
    res_df = st.session_state['res_df']
    
    # Filtreleme Seçeneği
    filter_option = st.selectbox(
        "Filtrele:",
        options=["Tümü", "Sadece AL Sinyali Verenler", "Aşırı Satış Tepki Kurulumları", "Aşırı Alım Bölgesi"]
    )
    
    if filter_option == "Sadece AL Sinyali Verenler":
        filtered_df = res_df[res_df["Sinyal Durumu"].str.contains("AL")]
    elif filter_option == "Aşırı Satış Tepki Kurulumları":
        filtered_df = res_df[res_df["Sinyal Durumu"].str.contains("AŞIRI SATIŞ")]
    elif filter_option == "Aşırı Alım Bölgesi":
        filtered_df = res_df[res_df["Sinyal Durumu"].str.contains("AŞIRI ALIM")]
    else:
        filtered_df = res_df

    st.dataframe(filtered_df, use_container_width=True)
    
    # CSV İndirme
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Sonuçları CSV Olarak İndir", csv, "bist_ichimoku_v29_tarama.csv", "text/csv")

# ==============================================================================
# İNTERAKTİF GRAFİK İNCELEME
# ==============================================================================
st.divider()
st.subheader("📊 Hisse Detay ve Ichimoku (v29) Grafiği")

selected_stock = st.selectbox("Grafiğini İncelemek İstediğiniz Hisseni Seçin:", options=[s.replace(".IS", "") for s in active_symbols])

if selected_stock:
    sym = selected_stock + ".IS"
    ticker = yf.Ticker(sym)
    df = ticker.history(period="1y")
    if not df.empty:
        calc_res = calculate_ichimoku_v29(df, tenkan_p, kijun_p, senkou_b_p)
        if calc_res:
            data = calc_res['data']
            
            fig = go.Figure()

            # Mum Grafiği
            fig.add_trace(go.Candlestick(
                x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
                name='Fiyat (Mum)'
            ))

            # Tenkan ve Kijun
            fig.add_trace(go.Scatter(x=data.index, y=data['tenkan'], line=dict(color='blue', width=1.5), name='Tenkan-sen (9)'))
            fig.add_trace(go.Scatter(x=data.index, y=data['kijun'], line=dict(color='red', width=2), name='Kijun-sen (26)'))

            # Senkou Span A ve B (Bulut)
            fig.add_trace(go.Scatter(x=data.index, y=data['senkou_a_future'], line=dict(color='green', width=1), name='Senkou Span A'))
            fig.add_trace(go.Scatter(x=data.index, y=data['senkou_b_future'], line=dict(color='maroon', width=1), fill='tonexty', name='Senkou Span B (Bulut)'))

            fig.update_layout(
                title=f"{selected_stock} - Ichimoku Kinko Hyo (v29) Analiz Grafiği",
                yaxis_title="Fiyat (TL)",
                xaxis_title="Tarih",
                template="plotly_white",
                height=600
            )

            st.plotly_chart(fig, use_container_width=True)
