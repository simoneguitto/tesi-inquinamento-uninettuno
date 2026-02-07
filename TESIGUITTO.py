import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- IMPOSTAZIONI ---
st.set_page_config(page_title="Simulatore Gas", layout="wide")
st.title("Simulazione Dispersione Gas e Ostacoli")
st.write("Analisi del movimento del gas tra palazzi e colline.")

# --- COMANDI LATERALI (MENU) ---
st.sidebar.header("Meteo e Vento")
aria = st.sidebar.selectbox("Tipo di Aria", ["Giorno (Movimentata)", "Standard", "Notte (Fermo)"])

if aria == "Giorno (Movimentata)":
    u_v, k_v = 1.2, 1.8 
elif aria == "Standard":
    u_v, k_v = 1.5, 1.0 
else:
    u_v, k_v = 0.6, 0.2

velocita = st.sidebar.slider("Velocità Vento", 0.1, 5.0, u_v)
diffusione = st.sidebar.slider("Allargamento Gas (K)", 0.1, 2.5, k_v)

st.sidebar.header("Pioggia e Sostanza")
pioggia = st.sidebar.select_slider("Intensità Pioggia", options=["Nessuna", "Debole", "Forte"])
tipo_sostanza = st.sidebar.selectbox("Sostanza Inquinante", ["Molto Solubile", "Media", "Poco Solubile"])

# Calcolo lavaggio pioggia
p_m = {"Nessuna": 0.0, "Debole": 0.1, "Forte": 0.25}[pioggia]
s_i = {"Molto Solubile": 1.0, "Media": 0.7, "Poco Solubile": 0.3}[tipo_sostanza]
soglia_allarme = 0.06 if tipo_sostanza == "Molto Solubile" else 0.12

# --- CREAZIONE MAPPA (PALAZZI E COLLINE) ---
N = 50
griglia_ostacoli = np.zeros((N, N))
griglia_colline = np.zeros((N, N))

# 1. Palazzi sparsi a caso (non a scacchiera)
griglia_ostacoli[8:12, 28:31] = 1   # Palazzo vicinissimo alla sorgente
griglia_ostacoli[25:28, 15:20] = 1  # Palazzo centrale
griglia_ostacoli[35:40, 30:33] = 1  # Palazzo lontano
griglia_ostacoli[15:18, 10:13] = 1  # Altro palazzo sparso

# 2. Due Colline
for i in range(N):
    for j in range(N):
        # Collina 1: Piccola e vicina alla sorgente
        d1 = np.sqrt((i-10)**2 + (j-15)**2)
        if d1 < 8: griglia_colline[i,j] += 2 * np.exp(-0.1 * d1**2)
        
        # Collina 2: Alta e lontana
        d2 = np.sqrt((i-40)**2 + (j-25)**2)
        if d2 < 15: griglia_colline[i,j] += 5 * np.exp(-0.03 * d2**2)

# --- CALCOLO MATEMATICO ---
if st.sidebar.button("AVVIA SIMULAZIONE"):
    C = np.zeros((N, N))
    mappa_display = st.empty()
    testo_display = st.empty()
    
    # Sorgente gas
    sx, sy = 5, 25 

    for t in range(160):
        Cn = C.copy()
        Cn[sx, sy] += 140 * 0.02 # Rilascio gas
        
        for i in range(1, N-1):
            for j in range(1, N-1):
                if griglia_ostacoli[i,j] == 1:
                    continue
                
                # Formule: Movimento + Allargamento - Pioggia
                diff = diffusione * 0.02 * (C[i+1,j] + C[i-1,j] + C[i,j+1] + C[i,j-1] - 4*C[i,j])
                adv = -velocita * 0.02 * (C[i,j] - C[i-1,j])
                reac = -(p_m * s_i) * 0.02 * C[i,j]
                
                Cn[i,j] += diff + adv + reac

        # Effetto aderenza ai palazzi (niente vuoto visivo)
        C = np.where(griglia_ostacoli == 1, 0, Cn)
        C = np.clip(C, 0, 100)
        
        if t % 15 == 0:
            picco_attuale = np.max(C[10:45, 10:45]) * 0.15
            
            # Grafico con scala colori Jet (Blu-Verde-Rosso)
            fig = go.Figure(data=[
                go.Surface(z=C + griglia_colline, colorscale='Jet', name="Gas"),
                go.Surface(z=griglia_ostacoli * 3.5, colorscale='Greys', opacity=0.8, showscale=False),
                go.Surface(z=griglia_colline, colorscale='Greens', opacity=0.3, showscale=False)
            ])
            
            fig.update_layout(
                scene=dict(zaxis=dict(range=[0, 15]), xaxis_title='Metri X', yaxis_title='Metri Y'),
                margin=dict(l=0, r=0, b=0, t=0), height=700
            )
            mappa_display.plotly_chart(fig, use_container_width=True)
            
            if picco_attuale > soglia_allarme:
                testo_display.error(f"SOGLIA SUPERATA: {picco_attuale:.4f} ppm")
            else:
                testo_display.success(f"LIVELLO SICURO: {picco_attuale:.4f} ppm")

    st.info("Simulazione conclusa. Il gas è stato deviato dai palazzi e dalle colline.")
