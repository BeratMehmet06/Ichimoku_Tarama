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
    page_title="BIST Ichimoku v30+ Canlı Tarama & Sinyal Motoru",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📈 BIST Ichimoku Kinko Hyo (v30) Canlı Tarama & Sinyal Motoru")
st.markdown("""
**Goichi Hosoda** felsefesi ve v30 gelişmiş strateji kuralları (Madde 1 Ana Alım, Madde 2a 10-Bar Hafızalı Aşırı Satış Tepki Alımı, Madde 2b Kısmi Alım, Madde 3 Engel Filtreleri ve Kijun-sen İz Sürer Stop Çıkış Yönetimi) ile **Borsa İstanbul 600+ Hisse Senedi ve BYF Canlı Tarayıcısı**.
""")

# ==============================================================================
# BIST KATEGORİK SEMBOL LİSTELERİ (600+ HİSSE VE BYF)
# ==============================================================================
BIST_30 = [
    "AKBNK.IS", "ALARK.IS", "ASELS.IS", "BIMAS.IS", "BRSAN.IS", "DOHOL.IS", "EKGYO.IS", "ENKAI.IS", "EREGL.IS", "FROTO.IS",
    "GARAN.IS", "GUBRF.IS", "HEKTS.IS", "ISCTR.IS", "KCHOL.IS", "KOZAL.IS", "KRDMD.IS", "ODAS.IS", "OYAKC.IS", "PETKM.IS",
    "PGSUS.IS", "SAHOL.IS", "SASA.IS", "SISE.IS", "TCELL.IS", "THYAO.IS", "TOASO.IS", "TUPRS.IS", "YKBNK.IS", "ZOREN.IS"
]

BIST_100_ADDITIONAL = [
    "AEFES.IS", "AGHOL.IS", "AHGAZ.IS", "AKFYE.IS", "AKSA.IS", "AKSEN.IS", "ALBRK.IS", "ALFAS.IS", "ANSGR.IS", "ARCLK.IS",
    "ARDYZ.IS", "ASTOR.IS", "BERA.IS", "BFREN.IS", "BIENP.IS", "BOBET.IS", "BRYAT.IS", "BSOKE.IS", "BUCIM.IS", "CANTE.IS",
    "CMENT.IS", "CWENE.IS", "DOAS.IS", "DSDHO.IS", "ECILC.IS", "EGEEN.IS", "ECZYT.IS", "EUPWR.IS", "GENIL.IS", "GESAN.IS",
    "GSDHO.IS", "GWIND.IS", "HALKB.IS", "INVEO.IS", "INVES.IS", "IPEKE.IS", "ISGYO.IS", "ISMEN.IS", "IZMDC.IS", "KARSN.IS",
    "KCAER.IS", "KMPUR.IS", "KONTR.IS", "KORDS.IS", "KOZAA.IS", "KZGYO.IS", "MAVI.IS", "MHRSG.IS", "MIATK.IS", "MPARK.IS",
    "OTKAR.IS", "OYYAT.IS", "PENTA.IS", "QUAGR.IS", "REEDR.IS", "RYSAS.IS", "SDTTR.IS", "SKBNK.IS", "SOKM.IS", "TABGD.IS",
    "TAVHL.IS", "TKFEN.IS", "TMSN.IS", "TSKB.IS", "TURSG.IS", "ULKER.IS", "VAKBN.IS", "VBTYZ.IS", "VESBE.IS", "VESTL.IS", "YEOTK.IS"
]

BIST_100 = list(dict.fromkeys(BIST_30 + BIST_100_ADDITIONAL))

BIST_OTHER = [
    "AAV.IS", "ACSEL.IS", "ADEL.IS", "ADESE.IS", "AFYON.IS", "AGESA.IS", "AGROT.IS", "AKENR.IS", "AKFGY.IS", "AKGRT.IS",
    "AKMGY.IS", "ALCAR.IS", "ALCTL.IS", "ALGYO.IS", "ALKA.IS", "ALKIM.IS", "ALMAD.IS", "ALPRI.IS", "ALTNY.IS", "ALVES.IS",
    "ANELE.IS", "ANGEN.IS", "ANHYT.IS", "ARASE.IS", "ARZUM.IS", "ATAGY.IS", "ATAKP.IS", "ATATP.IS", "ATEKS.IS", "ATSYH.IS",
    "AVHOL.IS", "AVOD.IS", "AVTUR.IS", "AYCES.IS", "AYDEM.IS", "AYEN.IS", "AYGAZ.IS", "AZTEK.IS", "BAGFS.IS", "BAKAB.IS",
    "BALAT.IS", "BANVT.IS", "BARMA.IS", "BASGZ.IS", "BAYRK.IS", "BEVT.IS", "BEYAZ.IS", "BICCS.IS", "BIGCH.IS", "BILICI.IS",
    "BINHO.IS", "BIOEN.IS", "BIZIM.IS", "BJKAS.IS", "BLCYO.IS", "BMSCH.IS", "BMSTL.IS", "BNTAS.IS", "BOSSA.IS", "BRISA.IS",
    "BRKO.IS", "BRKSN.IS", "BRMEN.IS", "BRKVY.IS", "BSEG.IS", "BTCIM.IS", "BURCE.IS", "BURVA.IS", "BVSAN.IS", "BYDNR.IS",
    "CAN.IS", "CASA.IS", "CATES.IS", "CCOLA.IS", "CELHA.IS", "CEMAS.IS", "CEMTS.IS", "CMBTN.IS", "CONSE.IS", "COSMO.IS",
    "CRDFA.IS", "CRFSA.IS", "CUSAN.IS", "CVKMD.IS", "DAGI.IS", "DAGHL.IS", "DAPGM.IS", "DARDL.IS", "DENGE.IS", "DERHL.IS",
    "DERIM.IS", "DESA.IS", "DESPC.IS", "DEVA.IS", "DGATE.IS", "DGGYO.IS", "DITAS.IS", "DMCOR.IS", "DNISI.IS", "DOCO.IS",
    "DOGUB.IS", "DURDO.IS", "DYOBY.IS", "EDATA.IS", "EDIP.IS", "EGGUB.IS", "EGSER.IS", "EIZAT.IS", "EKIZ.IS", "EKSUN.IS",
    "ELITE.IS", "EMKEL.IS", "EMNIS.IS", "ENERY.IS", "ENSRI.IS", "EPLAS.IS", "ERCB.IS", "ERBOS.IS", "ESCAR.IS", "ESEN.IS",
    "ETILR.IS", "EUKYO.IS", "EUHOL.IS", "EUYO.IS", "EYGYO.IS", "FADE.IS", "FENER.IS", "FLAP.IS", "FMIZP.IS", "FORMT.IS",
    "FORTE.IS", "FRIGO.IS", "FZLGY.IS", "GARFA.IS", "GEDIK.IS", "GEDZA.IS", "GENTAS.IS", "GEREL.IS", "GIPTA.IS", "GLBMD.IS",
    "GLYHO.IS", "GMTAS.IS", "GOKNR.IS", "GOLTS.IS", "GOODY.IS", "GOZDE.IS", "GRNYO.IS", "GRSEL.IS", "GSDDE.IS", "GSRAY.IS",
    "GURYR.IS", "HATEK.IS", "HATSN.IS", "HDFGS.IS", "HEDEF.IS", "HUBVC.IS", "HUNER.IS", "HURGZ.IS", "ICBCT.IS", "IDEAS.IS",
    "IDGYO.IS", "IEYHO.IS", "IHAAS.IS", "IHLGM.IS", "IHLAS.IS", "IHYO.IS", "IMASM.IS", "INDES.IS", "INFO.IS", "INGRM.IS",
    "INTEK.IS", "INTEM.IS", "ISATR.IS", "ISBTR.IS", "ISFIN.IS", "ISGSY.IS", "ISKPL.IS", "ISKUR.IS", "ISSEN.IS", "ITEKS.IS",
    "IZINV.IS", "IZFAS.IS", "JANTS.IS", "KAPLM.IS", "KARYE.IS", "KATMR.IS", "KAYSE.IS", "KBCOR.IS", "KBORU.IS", "KFEIN.IS",
    "KGYO.IS", "KIMMR.IS", "KLGYO.IS", "KLMSN.IS", "KLNMA.IS", "KLRZO.IS", "KLSYN.IS", "KNFRT.IS", "KONKA.IS", "KOPOL.IS",
    "KRDMA.IS", "KRDMB.IS", "KRGYO.IS", "KRONT.IS", "KRPLS.IS", "KRSTL.IS", "KRTEK.IS", "KRVGD.IS", "KSTUR.IS", "KTLEV.IS",
    "KTSKR.IS", "KUTPO.IS", "KUZEY.IS", "KUYAS.IS", "LIDER.IS", "LIDFA.IS", "LINK.IS", "LKMNH.IS", "LMOK.IS", "LUKSK.IS",
    "MAALT.IS", "MACKO.IS", "MAKIM.IS", "MAKTK.IS", "MANAS.IS", "MARKA.IS", "MARTI.IS", "MEGAP.IS", "MEGMT.IS", "MEPET.IS",
    "MERCN.IS", "MERIT.IS", "MERKO.IS", "METRO.IS", "METUR.IS", "MGDAR.IS", "MHRGY.IS", "MIPAZ.IS", "MMCAS.IS", "MNDTR.IS",
    "MNDRS.IS", "MOBTL.IS", "MTRKS.IS", "NATEN.IS", "NETAS.IS", "NIBAS.IS", "NTGAZ.IS", "NTHOL.IS", "NUGYO.IS", "NUHCM.IS",
    "OBAMS.IS", "OBASE.IS", "OFSYM.IS", "ONCSM.IS", "ORGE.IS", "ORMA.IS", "OSTIM.IS", "OYLUM.IS", "OZKGY.IS", "OZRDN.IS",
    "OZSUB.IS", "PAGYO.IS", "PAMEL.IS", "PAPIL.IS", "PARSN.IS", "PASEU.IS", "PCILT.IS", "PEKGY.IS", "PENGD.IS", "PKART.IS",
    "PKENT.IS", "PLTUR.IS", "PNLSN.IS", "PNSUT.IS", "POLHO.IS", "POLTK.IS", "PRDGS.IS", "PRKAB.IS", "PRKME.IS", "PRZMA.IS",
    "PSDTC.IS", "PSGYO.IS", "RAYSG.IS", "RGYO.IS", "RNPOL.IS", "RODRG.IS", "RUBNS.IS", "RYGYO.IS", "SAFKR.IS", "SAMAT.IS",
    "SANEL.IS", "SANFM.IS", "SANKO.IS", "SARKY.IS", "SAYAS.IS", "SEKFK.IS", "SEKUR.IS", "SELEC.IS", "SELVA.IS", "SEYKM.IS",
    "SILVR.IS", "SMRTG.IS", "SMART.IS", "SODSN.IS", "SONME.IS", "SRVGY.IS", "SUMAS.IS", "SUNTK.IS", "SURGY.IS", "SUWEN.IS",
    "TATEN.IS", "TATGD.IS", "TBORG.IS", "TCEVT.IS", "TDGYO.IS", "TEHOL.IS", "TEKFU.IS", "TETMT.IS", "TGSAS.IS", "TIRE.IS",
    "TKNSA.IS", "TLMAN.IS", "TNZTP.IS", "TRCAS.IS", "TRGYO.IS", "TRILC.IS", "TSPOR.IS", "TTRAK.IS", "TUCLK.IS", "TUKAS.IS",
    "TURGG.IS", "UFUK.IS", "ULAS.IS", "UNLU.IS", "USAK.IS", "VAKFA.IS", "VAKKO.IS", "VANGD.IS", "VERTU.IS", "VERUS.IS",
    "VKFYO.IS", "VKGYO.IS", "YAPRK.IS", "YATAS.IS", "YAYLA.IS", "YGGYO.IS", "YGYO.IS", "YONGA.IS", "YUNSA.IS", "YYLGD.IS", "ZEDUR.IS"
]

BYF_LIST = [
    "ZBYF.IS", "GLDTR.IS", "GMSTR.IS", "USDTR.IS", "FBK.IS", "ZGOLD.IS", "ZREOX.IS", "ZPLIB.IS", "ZROBOT.IS", "ZMETL.IS",
    "Z30EA.IS", "Z100A.IS", "FNSBA.IS", "ISE30.IS"
]

BIST_TUM = list(dict.fromkeys(BIST_100 + BIST_OTHER + BYF_LIST))
BIST_100_DISI = list(dict.fromkeys(BIST_OTHER + BYF_LIST))

# ==============================================================================
# ICHIMOKU V30 HESAPLAMA MOTORU (DİNAMİK ZAMAN DİLİMİ & 10-BAR HAFIZALI KONTROL)
# ==============================================================================
def calculate_ichimoku_v30(df, tenkan_len=9, kijun_len=26, senkou_b_len=52, displacement=26):
    if len(df) < senkou_b_len + displacement:
        return None

    high = df['High']
    low = df['Low']
    close = df['Close']
    open_p = df['Open']

    # Donchian Orta Noktaları
    tenkan = (high.rolling(window=tenkan_len).max() + low.rolling(window=tenkan_len).min()) / 2.0
    kijun = (high.rolling(window=kijun_len).max() + low.rolling(window=kijun_len).min()) / 2.0
    senkou_a = (tenkan + kijun) / 2.0
    senkou_b = (high.rolling(window=senkou_b_len).max() + low.rolling(window=senkou_b_len).min()) / 2.0

    # Tenkan Sapması (%)
    dev = ((close - tenkan) / tenkan) * 100.0

    res = df.copy()
    res['tenkan'] = tenkan
    res['kijun'] = kijun
    res['senkou_a'] = senkou_a
    res['senkou_b'] = senkou_b
    res['dev'] = dev

    # Senkou Span A/B (25 bar ileri kaydırılmış vizyon)
    res['senkou_a_curr'] = senkou_a.shift(displacement - 1)
    res['senkou_b_curr'] = senkou_b.shift(displacement - 1)

    # Chikou Span Onayı (25 bar önceki kapanış)
    res['close_prev_25'] = close.shift(displacement - 1)
    res['chikou_above'] = close > res['close_prev_25']

    # Madde 1 Temel Şartları (4/4 Boğa)
    res['cond_1a'] = (close > res['senkou_a_curr']) & (close > res['senkou_b_curr'])
    res['cond_1b'] = res['chikou_above']
    res['cond_1c'] = senkou_a > senkou_b
    res['cond_1d'] = tenkan > kijun
    res['base_rule_1'] = res['cond_1a'] & res['cond_1b'] & res['cond_1c'] & res['cond_1d']

    # Madde 2a: Aşırı Satış Tepki Alımı (10 Bar Kırılım Takip Hafızası)
    is_oversold = dev <= -20.0
    res['oversold_trigger'] = False
    
    # 10 bar içinde oversold olmuş ve tepe kırılımı vermiş mi kontrolü
    for i in range(len(res) - 1, max(0, len(res) - 15), -1):
        if is_oversold.iloc[i]:
            ref_high = high.iloc[i]
            # son barlarda tepe kırılmış mı
            if high.iloc[-1] >= ref_high or close.iloc[-1] > ref_high:
                res.loc[res.index[-1], 'oversold_trigger'] = True
                break

    # Madde 2b: 4 Şarttan En Az 3'ü + Yön Yukarı
    cond_count = res['cond_1a'].astype(int) + res['cond_1b'].astype(int) + res['cond_1c'].astype(int) + res['cond_1d'].astype(int)
    has_3_of_4 = cond_count >= 3
    senkou_b_rising = senkou_b > senkou_b.shift(1)
    tenkan_rising = tenkan > tenkan.shift(1)
    res['rule_2b_met'] = has_3_of_4 & senkou_b_rising & tenkan_rising

    # Madde 3 Engelleme Filtreleri
    cloud_thickness_pct = (np.abs(senkou_a - senkou_b) / close) * 100.0
    res['filter_thin_cloud'] = cloud_thickness_pct < 0.3

    is_flat_kijun = (kijun.rolling(5).max() == kijun.rolling(5).min())
    is_flat_senkou_b = (senkou_b.rolling(5).max() == senkou_b.rolling(5).min())
    res['filter_flat_line'] = is_flat_kijun | is_flat_senkou_b

    res['filter_overbought'] = dev >= 20.0

    dist_to_tenkan_pct = np.abs((close - tenkan) / tenkan) * 100.0
    is_near_tenkan = dist_to_tenkan_pct <= 10.0
    touched_tk = (low <= tenkan) | (low <= kijun)
    is_bounce = (close > open_p) | (close > close.shift(1))
    res['tenkan_proximity'] = is_near_tenkan | (touched_tk & is_bounce)

    res['no_buy_filter'] = res['filter_thin_cloud'] | res['filter_overbought']

    # Sinyal Tespiti (Son Bar)
    n = len(res) - 1
    last_row = res.iloc[n]
    
    signal = "NÖTR"
    signal_color = "gray"
    reason = "Şartlar henüz tam oluşmadı"

    # KRİTİK ÇIKIŞ KONTROLÜ: Fiyat Kijun-sen altındaysa KESİNLİKLE AL DENMEZ (KAPAT / SAT verilir)
    if last_row['Close'] < last_row['kijun']:
        signal = "KAPAT / SAT (Kijun Altı Kapanış)"
        signal_color = "red"
        reason = f"Fiyat ({round(last_row['Close'], 2)} TL) Kijun-sen ({round(last_row['kijun'], 2)} TL) altına sarktı! İz sürer stop aktif."
    elif last_row['base_rule_1'] and not last_row['no_buy_filter']:
        # Taptaze kırılım mı kontrolü (Önceki bar base_rule_1 değilse yeni)
        is_fresh = not res.iloc[n-1]['base_rule_1'] if n > 0 else True
        if is_fresh:
            signal = "🔥 AL (Madde 1 - YENİ Kırılım)"
            signal_color = "green"
            reason = "Bugün 4/4 Tam Boğa Hizalanması Taptaze Oluştu!"
        else:
            signal = "AL (Madde 1 - Yükseliş Trendinde)"
            signal_color = "green"
            reason = "Fiyat bulut, Kijun ve Tenkan üstünde boğa konumunu koruyor."
    elif last_row['oversold_trigger']:
        signal = "🚀 AL (Madde 2a - Aşırı Satış Tepki Alımı)"
        signal_color = "orange"
        reason = "Aşırı satış dip kırılımı gerçekleşti! 1:2 RR hefilli tepki alımı."
    elif last_row['rule_2b_met'] and not last_row['no_buy_filter']:
        signal = "⚡ AL (Madde 2b - 3/4 Şart + Yön Yukarı)"
        signal_color = "blue"
        reason = "En az 3 şart sağlandı ve dönüş yönü yukarı gerçekleşti."
    elif last_row['filter_overbought']:
        signal = "⚠️ AŞIRI ALIM UYARISI"
        signal_color = "purple"
        reason = "Tenkan-sen Sapması >= %20 (Kâr Alım Çıkışı Takip Edilmeli)"

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
# YAN MENÜ (SIDEBAR) & TARAMA PARAMETRELERİ
# ==============================================================================
st.sidebar.header("⚙️ Tarama & Filtre Ayarları")

category_choice = st.sidebar.selectbox(
    "📌 Hisse / Kategori Seçimi:",
    options=[
        "BIST TÜM & BYF'ler (Tüm Hisseler - ~600+)",
        "BIST 30 (Majör Hisseler)",
        "BIST 100 (Ana Hisseler)",
        "BIST 100 Dışı (Küçük / Orta Ölçekli Hisseler)",
        "BYF'ler (Borsa Yatırım Fonları)",
        "Özel Liste / Sembol Gir"
    ]
)

timeframe_choice = st.sidebar.selectbox(
    "⏱️ Zaman Dilimi (Periyot):",
    options=["Günlük (1D)", "4 Saatlik (4H)", "Haftalık (1W)"]
)

if category_choice == "BIST TÜM & BYF'ler (Tüm Hisseler - ~600+)":
    active_symbols = BIST_TUM
elif category_choice == "BIST 30 (Majör Hisseler)":
    active_symbols = BIST_30
elif category_choice == "BIST 100 (Ana Hisseler)":
    active_symbols = BIST_100
elif category_choice == "BIST 100 Dışı (Küçük / Orta Ölçekli Hisseler)":
    active_symbols = BIST_100_DISI
elif category_choice == "BYF'ler (Borsa Yatırım Fonları)":
    active_symbols = BYF_LIST
else:
    custom_text = st.sidebar.text_area("İstediğiniz sembolleri yazın (örn: THYAO, SASA, CAN, TEHOL):", value="THYAO, GARAN, ASELS, SASA, CAN, TEHOL")
    user_syms = [s.strip().upper() + (".IS" if not s.strip().upper().endswith(".IS") else "") for s in custom_text.split(",") if s.strip()]
    active_symbols = user_syms

st.sidebar.markdown(f"**Seçilen Sembol Sayısı:** `{len(active_symbols)}` adet")

tenkan_p = st.sidebar.number_input("Tenkan-sen Periyodu", value=9, min_value=1)
kijun_p = st.sidebar.number_input("Kijun-sen Periyodu", value=26, min_value=1)
senkou_b_p = st.sidebar.number_input("Senkou Span B Periyodu", value=52, min_value=1)

# ==============================================================================
# CANLI TARAMA MOTORU
# ==============================================================================
st.subheader(f"🔍 BIST Canlı Tarama Sonuçları ({category_choice} - {timeframe_choice})")

if timeframe_choice == "Günlük (1D)":
    period_str, interval_str = "1y", "1d"
elif timeframe_choice == "4 Saatlik (4H)":
    period_str, interval_str = "60d", "1h"
else:
    period_str, interval_str = "2y", "1wk"

if st.button("🚀 Taramayı Başlat", type="primary"):
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Hızlı Toplu İndirme veya Parçalı Tarama (Batching)
    batch_size = 50
    total_batches = (len(active_symbols) + batch_size - 1) // batch_size
    
    for b_idx in range(total_batches):
        batch_syms = active_symbols[b_idx * batch_size : (b_idx + 1) * batch_size]
        status_text.text(f"Veriler Çekiliyor... ({b_idx * batch_size + len(batch_syms)} / {len(active_symbols)} sembol)")
        
        try:
            batch_data = yf.download(batch_syms, period=period_str, interval=interval_str, group_by="ticker", threads=True, progress=False)
            
            for sym in batch_syms:
                try:
                    if len(batch_syms) == 1:
                        df = batch_data.copy()
                    else:
                        df = batch_data[sym].dropna() if sym in batch_data else pd.DataFrame()
                    
                    if not df.empty and len(df) >= senkou_b_p + 26:
                        # 4h Resampling if 1h data fetched
                        if timeframe_choice == "4 Saatlik (4H)":
                            df = df.resample('4h').agg({
                                'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
                            }).dropna()

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
                except Exception as ex:
                    pass
        except Exception as e:
            pass
            
        progress_bar.progress((b_idx + 1) / total_batches)

    status_text.text("Tarama Tamamlandı!")
    
    if results:
        res_df = pd.DataFrame(results)
        st.session_state['res_df'] = res_df
        st.success(f"Tarama Tamamlandı! Toplam {len(results)} sembol başarıyla analiz edildi.")
    else:
        st.error("Veriler çekilemedi veya seçilen kriterlerde sembol bulunamadı.")

# ==============================================================================
# SONUÇLARI FİLTRELEME VE GÖRSELLEŞTİRME
# ==============================================================================
if 'res_df' in st.session_state:
    res_df = st.session_state['res_df']
    
    filter_option = st.selectbox(
        "🎯 Sinyal Filtresi:",
        options=[
            "Tümü",
            "Sadece AL Sinyali Verenler (Tüm AL Türleri)",
            "🔥 Sadece YENİ AL Kırılımı Yapanlar",
            "🚀 Aşırı Satış Tepki Alımları (Madde 2a)",
            "🛑 KAPAT / SAT Sinyali Verenler (Kijun Altı)"
        ]
    )
    
    if filter_option == "Sadece AL Sinyali Verenler (Tüm AL Türleri)":
        filtered_df = res_df[res_df["Sinyal Durumu"].str.contains("AL")]
    elif filter_option == "🔥 Sadece YENİ AL Kırılımı Yapanlar":
        filtered_df = res_df[res_df["Sinyal Durumu"].str.contains("YENİ Kırılım")]
    elif filter_option == "🚀 Aşırı Satış Tepki Alımları (Madde 2a)":
        filtered_df = res_df[res_df["Sinyal Durumu"].str.contains("Aşırı Satış")]
    elif filter_option == "🛑 KAPAT / SAT Sinyali Verenler (Kijun Altı)":
        filtered_df = res_df[res_df["Sinyal Durumu"].str.contains("KAPAT / SAT")]
    else:
        filtered_df = res_df

    st.dataframe(filtered_df, use_container_width=True)

    # CSV İndirme Butonu
    csv_data = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Tarama Sonuçlarını CSV Olarak İndir",
        data=csv_data,
        file_name=f"BIST_Ichimoku_Tarama_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime='text/csv'
    )

    # Detaylı Grafik Görselleştirme
    st.markdown("---")
    st.subheader("📊 Hisse Detaylı Grafik ve Ichimoku İncelemesi")
    
    selected_symbol_name = st.selectbox("Grafiğini İncelemek İstediğiniz Hissiyi Seçin:", options=filtered_df["Hisse / Sembol"].tolist())
    
    if selected_symbol_name:
        full_sym = selected_symbol_name + ".IS"
        try:
            ticker = yf.Ticker(full_sym)
            chart_df = ticker.history(period=period_str, interval=interval_str)
            if not chart_df.empty:
                if timeframe_choice == "4 Saatlik (4H)":
                    chart_df = chart_df.resample('4h').agg({
                        'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
                    }).dropna()

                # Ichimoku Çizgileri
                c_tenkan = (chart_df['High'].rolling(9).max() + chart_df['Low'].rolling(9).min()) / 2.0
                c_kijun = (chart_df['High'].rolling(26).max() + chart_df['Low'].rolling(26).min()) / 2.0
                c_senkou_a = (c_tenkan + c_kijun) / 2.0
                c_senkou_b = (chart_df['High'].rolling(52).max() + chart_df['Low'].rolling(52).min()) / 2.0

                fig = go.Figure()

                # Mum Grafiği
                fig.add_trace(go.Candlestick(
                    x=chart_df.index,
                    open=chart_df['Open'], high=chart_df['High'],
                    low=chart_df['Low'], close=chart_df['Close'],
                    name="Mumlar"
                ))

                # Tenkan & Kijun
                fig.add_trace(go.Scatter(x=chart_df.index, y=c_tenkan, mode='lines', line=dict(color='blue', width=1.5), name='Tenkan-sen (9)'))
                fig.add_trace(go.Scatter(x=chart_df.index, y=c_kijun, mode='lines', line=dict(color='red', width=2), name='Kijun-sen (26)'))

                fig.update_layout(
                    title=f"{selected_symbol_name} - Ichimoku Kinko Hyo Grafiği ({timeframe_choice})",
                    yaxis_title="Fiyat (TL)",
                    xaxis_title="Tarih",
                    template="plotly_dark",
                    height=600
                )
                st.plotly_chart(fig, use_container_width=True)
        except Exception as ex:
            st.warning("Grafik verisi çekilirken bir sorun oluştu.")
