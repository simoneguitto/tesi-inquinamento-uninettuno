import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Simulatore Meteo-Urbano Avanzato", layout="wide")

st.title("Sistema Integrato di Simulazione Dispersione Atmosferica")
st.write("Analisi ADR con ostacoli a volumetria variabile (altezze reali differenziate).")

# --- SIDEBAR: CONTROLLO SCENARIO ---
st.sidebar.header("🏢 Configurazione Urbanistica")
num_palazzi = st.sidebar.slider("Numero di Palazzi", 0, 10, 5)
dist_primo_palazzo = st.sidebar.slider("Distanza Primo Palazzo (m)", 8, 20, 12)

st.sidebar.header("⛰️ Configurazione Orografica")
num_colline = st.sidebar.slider("Numero di Colline", 0, 5, 2)
altezza_max_colline = st.sidebar.slider("Altezza Rilievi (m)", 2.0, 10.0, 5.0)

st.sidebar.header("🌦️ Parametri Meteorologici")
v_kmh = st.sidebar.slider("Velocità Vento (km/h)", 1.0, 40.0, 10.0)
u_vento = v_kmh / 3.6 

mm_pioggia = st.sidebar.slider("Intensità Pioggia (mm/h)", 0, 100, 0)
k_diff = st.sidebar.slider("Diffusione Turbolenta (K)", 0.1, 2.5, 1.0)

# --- LOGICA DI CALCOLO ---
sigma_pioggia = (mm_pioggia / 100) * 0.4 

# --- CREAZIONE MAPPA CON ALTEZZE REALI ---
N = 50
edifici_mask = np.zeros((N, N)) # Dove sono i palazzi
edifici_altezze = np.zeros((N, N)) # Quanto sono alti
orografia = np.zeros((N, N))

np.random.seed(42)
if num_palazzi > 0:
    # 1. IL PRIMO PALAZZO (Sempre Altissimo: 12 metri)
    edifici_mask[dist_primo_palazzo:dist_primo_palazzo+4, 23:27] = 1
    edifici_altezze[dist_primo_palazzo:dist_primo_palazzo+4, 23:27] = 12.0
    
    # 2. GLI ALTRI PALAZZI (Altezze variabili tra 2 e 10 metri)
    for _ in range(num_palazzi - 1):
        px, py = np.random.randint(15, 45), np.random.randint(10, 40)
        h_casuale = np.random.uniform(2.0, 10.0)
        edifici_mask[px:px+3, py:py+3] = 1
        edifici_altezze[px:px+3, py:py+3] = h_casuale

if num_colline > 0:
    for c in range(num_colline):
        cx = 10 if c == 0 else np.random.randint(20, 45)
        cy = 15 if c == 0 else np.random.randint(10, 40)
        h = altezza_max_colline * (0.6 + np.random.rand() * 0.4)
        for i in range(N):
            for j in range(N):
                dist = np.sqrt((i-cx)**2 + (j-cy)**2)
                if dist < 12:
                    orografia[i,j] += h * np.exp(-0.07 * dist**2)

# --- MOTORE DI CALCOLO ---
if st.sidebar.button("ESEGUI ANALISI METEOROLOGICA"):
    C = np.zeros((N, N))
    mappa_box = st.empty()
    testo_box = st.empty()
    sx, sy = 5, 25 

    for t in range(160):
        Cn = C.copy()
        Cn[sx, sy] += 160 * dt = 0.02 # dt definito qui per sicurezza
        
        for i in range(1, N-1):
            for j in range(1, N-1):
                if edifici_mask[i,j] == 1: continue
                diff = k_diff * 0.02 * (C[i+1,j] + C[i-1,j] + C[i,j+1] + C[i,j-1] - 4*C[i,j])
                adv = -u_vento * 0.02 * (C[i,j] - C[i-1,j])
                reac = -sigma_pioggia * 0.02 * C[i,j]
                Cn[i,j] += diff + adv + reac

        C = np.where(edifici_mask == 1, 0, Cn)
        C = np.clip(C, 0, 100)
        
        if t % 15 == 0:
            picco = np.max(C) * 0.15
            fig = go.Figure(data=[
                go.Surface(z=C + orografia, colorscale='Jet', cmin=0.01, cmax=12, name="Gas"),
                # VISUALIZZAZIONE ALTEZZE REALI DEI PALAZZI
                go.Surface(z=edifici_altezze, colorscale='Greys', opacity=0.9, showscale=False),
                go.Surface(z=orografia, colorscale='Greens', opacity=0.3, showscale=False)
            ])
            fig.update_layout(
                scene=dict(
                    zaxis=dict(range=[0, 15]), 
                    xaxis_title="X (m)", yaxis_title="Y (m)"
                ),
                margin=dict(l=0, r=0, b=0, t=0), height=700
            )
            mappa_box.plotly_chart(fig, use_container_width=True)
            
            if picco > 0.12: testo_box.error(f"⚠️ SOGLIA CRITICA: {picco:.4f} ppm")
            else: testo_box.success(f"✅ STATO SICURO: {picco:.4f} ppm")

    st.info("Simulazione completata con volumetrie differenziate per Uninettuno.")
