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
    page_title="BIST Ichimoku v30 Canlı Taraması",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📈 BIST Ichimoku Kinko Hyo (v30) Canlı Tarama & Sinyal Motoru")
st.markdown("""
**Goichi Hosoda** felsefesi ve v30 gelişmiş strateji kuralları (Madde 1 Ana Alım, Madde 2a Aşırı Satış Tepki Alımı, Madde 2b Kısmi Alım, Madde 3 Engel Filtreleri ve **Kijun Kırılım Çıkış / KAPAT Yönetimi**) ile Borsa İstanbul hisse senedi ve BYF canlı tarayıcısı.
""")

# ==============================================================================
# BIST GENİŞLETİLMİŞ SEMBOL LİSTESİ
# ==============================================================================
DEFAULT_SYMBOLS = [
    "THYAO.IS", "GARAN.IS", "EREGL.IS", "AKBNK.IS", "ISCTR.IS",
    "SAHOL.IS", "KCHOL.IS", "BIMAS.IS", "ASELS.IS", "TUPRS.IS",
    "SISE.IS", "EKGYO.IS", "YKBNK.IS", "ENKAI.IS", "DOHOL.IS",
    "PETKM.IS", "TOASO.IS", "FROTO.IS", "TTKOM.IS", "TCELL.IS",
    "HEKTS.IS", "GUBRF.IS", "SASA.IS", "ALARK.IS", "ODAS.IS",
    "KOZAL.IS", "KOZAA.IS", "IPEKE.IS", "VESTL.IS", "VESBE.IS",
    "ALVES.IS", "CAN.IS", "TEHOL.IS", "ASTOR.IS", "KONTR.IS",
    "MIATK.IS", "REEDR.IS", "SMMAS.IS", "ZBYF.IS"
]

# ==============================================================================
# ICHIMOKU V30 HESAPLAMA VE SİNYAL MOTORU
# ==============================================================================
def calculate_ichimoku_v30(df, tenkan_len=9, kijun_len=26, senkou_b_len=52, displacement=26):
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

    # Tenkan Sapması (%)
    dev = ((close - tenkan) / tenkan) * 100.0

    # Bulut Değerleri (Zaman Kaydırmalı)
    senkou_a_curr = senkou_a.shift(displacement - 1)
    senkou_b_curr = senkou_b.shift(displacement - 1)

    # Chikou Span Onayı (25 bar önceki kapanışa kıyasla)
    close_prev_25 = close.shift(displacement - 1)
    chikou_above = close > close_prev_25

    # DataFrame Yapılandırması
    res = df.copy()
    res['tenkan'] = tenkan
    res['kijun'] = kijun
    res['senkou_a'] = senkou_a
    res['senkou_b'] = senkou_b
    res['senkou_a_curr'] = senkou_a_curr
    res['senkou_b_curr'] = senkou_b_curr
    res['dev'] = dev

    # Madde 1 Temel Şartları:
    # 1. Fiyat Kumo Bulutunun Üstünde (close > senkou_a_curr ve close > senkou_b_curr)
    # 2. Fiyat Kijun-sen'in Üstünde (close > kijun) -> ASELS DÜZELTMESİ!
    # 3. Chikou Span Onaylı (close > close_25_bars_ago)
    # 4. Tenkan > Kijun
    # 5. Gelecek Bulutu Yeşil (senkou_a > senkou_b)
    cond_cloud_above = (close > senkou_a_curr) & (close > senkou_b_curr)
    cond_price_above_kijun = close > kijun
    cond_chikou = chikou_above
    cond_tk_cross = tenkan > kijun
    cond_green_cloud = senkou_a > senkou_b

    base_rule_1 = cond_cloud_above & cond_price_above_kijun & cond_chikou & cond_tk_cross & cond_green_cloud

    # Çıkış / KAPAT Şartları (Kijun Kırılımı):
    exit_kijun = close < kijun

    # Filtreler (Madde 3):
    cloud_thickness_pct = (np.abs(senkou_a - senkou_b) / close) * 100.0
    filter_thin_cloud = cloud_thickness_pct < 0.3
    filter_overbought = dev >= 20.0
    is_oversold = dev <= -20.0

    n = len(res) - 1
    last_row = res.iloc[n]

    last_close = last_row['Close']
    last_tenkan = last_row['tenkan']
    last_kijun = last_row['kijun']
    last_dev = last_row['dev']

    signal = "NÖTR"
    signal_color = "gray"
    reason = "Şartlar oluşmadı"

    if exit_kijun.iloc[n]:
        signal = "KAPAT / SAT (Kijun Altı Kapanış)"
        signal_color = "red"
        reason = f"Fiyat ({last_close:.2f} TL) Kijun-sen ({last_kijun:.2f} TL) altına sarktı! İz sürer stop aktif."
    elif base_rule_1.iloc[n] and not filter_overbought.iloc[n] and not filter_thin_cloud.iloc[n]:
        if not base_rule_1.iloc[n-1]:
            signal = "🔥 YENİ AL (Madde 1 - Ana Alım)"
            signal_color = "green"
            reason = "Taptaze 4/4 Tam Boğa Hizalanması + Filtre Onayı!"
        else:
            signal = "AL (Madde 1 - Yükseliş Trendinde)"
            signal_color = "green"
            reason = "Fiyat bulut, Kijun ve Tenkan üstünde boğa konumunu koruyor."
    elif is_oversold.iloc[n]:
        signal = "⚡ AŞIRI SATIŞ UYARISI (Madde 2a)"
        signal_color = "orange"
        reason = f"Tenkan Sapması ({last_dev:.1f}%) <= -%20. Tepki alımı kırılımı bekleniyor."
    elif filter_overbought.iloc[n]:
        signal = "⚠️ AŞIRI ALIM BÖLGESİ"
        signal_color = "purple"
        reason = f"Tenkan Sapması ({last_dev:.1f}%) >= %20. Yeni alım engelli, kâr al takip edilmeli."
    elif cond_tk_cross.iloc[n] and not cond_cloud_above.iloc[n]:
        signal = "NÖTR (Bulut İçi / Altı)"
        signal_color = "gray"
        reason = "Tenkan > Kijun ancak fiyat Kumo bulutunun üstüne çıkamadı."

    return {
        'data': res,
        'last_close': last_close,
        'last_tenkan': last_tenkan,
        'last_kijun': last_kijun,
        'dev_pct': last_dev,
        'signal': signal,
        'signal_color': signal_color,
        'reason': reason
    }

# ==============================================================================
# YAN MENÜ (SIDEBAR) & ZAMAN DİLİMİ AYARLARI
# ==============================================================================
st.sidebar.header("⏱️ Zaman Dilimi & Ayarlar")

tf_option = st.sidebar.selectbox(
    "Zaman Dilimi (Period):",
    options=["Günlük (1D)", "4 Saatlik (4H)", "Haftalık (1W)"],
    index=0
)

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
st.subheader(f"🔍 BIST Canlı Tarama Sonuçları ({tf_option})")

if st.button("🚀 Taramayı Başlat", type="primary"):
    results = []
    progress_bar = st.progress(0)
    
    # Zaman dilimine göre yfinance veri çekme parametreleri
    if tf_option == "Günlük (1D)":
        hist_period, hist_interval = "1y", "1d"
    elif tf_option == "Haftalık (1W)":
        hist_period, hist_interval = "2y", "1wk"
    else: # 4H
        hist_period, hist_interval = "60d", "60m"

    for idx, sym in enumerate(active_symbols):
        try:
            ticker = yf.Ticker(sym)
            df = ticker.history(period=hist_period, interval=hist_interval)
            
            # 4 Saatlik Zaman Dilimi İse 60m Verisini 4H'a Dönüştür
            if tf_option == "4 Saatlik (4H)" and not df.empty:
                df = df.resample('4h').agg({
                    'Open': 'first',
                    'High': 'max',
                    'Low': 'min',
                    'Close': 'last',
                    'Volume': 'sum'
                }).dropna()

            if not df.empty and len(df) >= 80:
                res = calculate_ichimoku_v30(df, tenkan_p, kijun_p, senkou_b_p)
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
        st.success(f"Tarama Tamamlandı! Toplam {len(results)} sembol {tf_option} periyodunda analiz edildi.")

if 'res_df' in st.session_state:
    res_df = st.session_state['res_df']
    
    # Filtreleme Seçeneği
    filter_option = st.selectbox(
        "Sinyal Filtresi:",
        options=["Tümü", "Sadece AL Sinyali Verenler", "KAPAT / SAT Sinyali Verenler", "Aşırı Satış Tepki Kurulumları", "Aşırı Alım Bölgesi"]
    )
    
    if filter_option == "Sadece AL Sinyali Verenler":
        filtered_df = res_df[res_df["Sinyal Durumu"].str.contains("AL")]
    elif filter_option == "KAPAT / SAT Sinyali Verenler":
        filtered_df = res_df[res_df["Sinyal Durumu"].str.contains("KAPAT")]
    elif filter_option == "Aşırı Satış Tepki Kurulumları":
        filtered_df = res_df[res_df["Sinyal Durumu"].str.contains("AŞIRI SATIŞ")]
    elif filter_option == "Aşırı Alım Bölgesi":
        filtered_df = res_df[res_df["Sinyal Durumu"].str.contains("AŞIRI ALIM")]
    else:
        filtered_df = res_df

    st.dataframe(filtered_df, use_container_width=True)
    
    # CSV İndirme
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Sonuçları CSV Olarak İndir",
        data=csv,
        file_name=f"bist_ichimoku_v30_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )

st.markdown("---")
st.caption("Ichimoku Kinko Hyo v30 Strateji Engine | Borsa İstanbul Canlı Veri Taraması")
