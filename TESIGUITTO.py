import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Analisi Dispersione Atmosferica", layout="wide")
st.title("Modello ADR: Impatto Meteorologico e Morfologico")
st.write("Simulazione della dispersione gas in presenza di ostacoli topografici e rilievi.")

# --- SIDEBAR: METEOROLOGIA ---
st.sidebar.header("Parametri Atmosferici")
clima = st.sidebar.selectbox("Stabilità dell'aria", ["Turbolenta (Giorno)", "Standard", "Stabile (Inversione)"])

if clima == "Turbolenta (Giorno)":
    u_base, k_base = 1.0, 1.9 
elif clima == "Standard":
    u_base, k_base = 1.5, 1.0 
else:
    u_base, k_base = 0.5, 0.25 

v_vento = st.sidebar.slider("Velocità del vento (u) [m/s]", 0.1, 5.0, u_base)
k_diff = st.sidebar.slider("Coefficiente di diffusione (K)", 0.1, 2.5, k_base)

st.sidebar.header("Variabili di Rimozione")
pioggia_liv = st.sidebar.select_slider("Livello Precipitazione", options=["Zero", "Media", "Forte"])
solub_gas = st.sidebar.selectbox("Solubilità Inquinante", ["Alta", "Media", "Bassa"])

# Parametri chimico-fisici
s_wash = {"Zero": 0.0, "Media": 0.12, "Forte": 0.26}[pioggia_liv]
s_idx = {"Alta": 1.0, "Media": 0.7, "Bassa": 0.3}[solub_gas]
soglia_safe = 0.06 if solub_gas == "Alta" else 0.14

# --- GRIGLIA E MAPPA (TOPOGRAFIA/OROGRAFIA) ---
N = 50
dx, dt = 1.0, 0.02
step_t = 165

edifici = np.zeros((N, N))
colline = np.zeros((N, N))

# 1. TOPOGRAFIA: Palazzi sparsi (Il primo è in traiettoria diretta)
edifici[18:24, 23:26] = 1  # Palazzo frontale (impatto diretto)
edifici[10:14, 12:15] = 1  # Palazzo laterale alto
edifici[32:36, 18:22] = 1  # Palazzo centrale
edifici[28:34, 38:42] = 1  # Palazzo lontano

# 2. OROGRAFIA: Due colline (Vicina e Lontana)
for i in range(N):
    for j in range(N):
        # Collina piccola (vicino sorgente)
        d1 = np.sqrt((i-8)**2 + (j-18)**2)
        if d1 < 8: colline[i,j] += 2.5 * np.exp(-0.12 * d1**2)
        # Collina grande (barriera di fondo)
        d2 = np.sqrt((i-43)**2 + (j-25)**2)
        if d2 < 15: colline[i,j] += 5.8 * np.exp(-0.04 * d2**2)

# --- MOTORE DI CALCOLO ---
if st.sidebar.button("AVVIA SIMULAZIONE"):
    C = np.zeros((N, N))
    mappa_box = st.empty()
    testo_box = st.empty()
    
    # Sorgente emissione
    sx, sy = 5, 25 

    for t in range(step_t):
        Cn = C.copy()
        Cn[sx, sy] += 140 * dt # Emissione continua
        
        for i in range(1, N-1):
            for j in range(1, N-1):
                if edifici[i,j] == 1:
                    continue
                
                # Formula ADR (Equazione della tesi)
                diff = k_diff * dt * (C[i+1,j] + C[i-1,j] + C[i,j+1] + C[i,j-1] - 4*C[i,j])
                adv = -v_vento * dt * (C[i,j] - C[i-1,j])
                reac = -(s_wash * s_idx) * dt * C[i,j]
                
                Cn[i,j] += diff + adv + reac

        # Aderenza alle pareti (eliminazione del bianco/vuoto)
        C = np.where(edifici == 1, 0, Cn)
        C = np.clip(C, 0, 100)
        
        if t % 15 == 0:
            p_ppm = np.max(C[10:45, 10:45]) * 0.15
            
            # Grafico con colori fissi per evitare lo "sbiancamento"
            fig = go.Figure(data=[
                go.Surface(
                    z=C + colline, 
                    colorscale='Jet', 
                    showscale=True, 
                    cmin=0, cmax=12,  # Blocca il colore per non diventare bianco
                    name="Gas"
                ),
                go.Surface(z=edifici * 4.0, colorscale='Greys', opacity=0.9, showscale=False),
                go.Surface(z=colline, colorscale='Greens', opacity=0.3, showscale=False)
            ])
            
            fig.update_layout(
                scene=dict(
                    zaxis=dict(range=[0, 15], title="Concentrazione [ppm]"),
                    xaxis_title="X [m]", yaxis_title="Y [m]"
                ),
                margin=dict(l=0, r=0, b=0, t=0), height=750
            )
            mappa_box.plotly_chart(fig, use_container_width=True)
            
            if p_ppm > soglia_safe:
                testo_box.error(f"⚠️ SOGLIA CRITICA: {p_ppm:.4f} ppm - Impatto su edifici rilevato")
            else:
                testo_box.success(f"✅ STATO SICURO: {p_ppm:.4f} ppm")

    st.info("Analisi completata. Il modello mostra l'interazione tra meteorologia, topografia urbana e orografia.")
