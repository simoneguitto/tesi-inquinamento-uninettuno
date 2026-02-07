import streamlit as st
import numpy as np
import plotly.graph_objects as go
import base64

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Simulatore Meteo Uninettuno", layout="wide")

# --- FUNZIONE PER IL LOGO (METODO SICURO) ---
def get_image_as_base64(url):
    # Questa stringa rappresenta il logo Uninettuno in formato testo
    # Se il link fallisce, usiamo un segnaposto testuale elegante
    return f'<div style="text-align: center;"><h2 style="color: #0056b3;">UNINETTUNO</h2><p>Simulatore Dispersione</p></div>'

# Inseriamo il logo o il titolo nella sidebar
st.sidebar.markdown(get_image_as_base64(""), unsafe_allow_html=True)
st.sidebar.markdown("---")

# --- INTESTAZIONE PRINCIPALE ---
st.title("Sistema Integrato di Simulazione Dispersione Atmosferica")
st.write("Analisi dell'impatto di inquinanti in funzione di topografia, orografia e precipitazioni.")

# --- SIDEBAR: CONTROLLO SCENARIO ---
st.sidebar.header("🏢 Configurazione Urbanistica")
num_palazzi = st.sidebar.slider("Numero di Palazzi", 0, 10, 4)
dist_primo_palazzo = st.sidebar.slider("Distanza Primo Palazzo (m)", 8, 20, 12)

st.sidebar.header("⛰️ Configurazione Orografica")
num_colline = st.sidebar.slider("Numero di Colline", 0, 5, 2)
altezza_max_colline = st.sidebar.slider("Altezza Rilievi (m)", 2.0, 10.0, 5.0)

st.sidebar.header("🌦️ Parametri Meteorologici")
v_kmh = st.sidebar.slider("Velocità Vento (km/h)", 1.0, 20.0, 8.0)
u_vento = v_kmh / 3.6 

mm_pioggia = st.sidebar.slider("Intensità Pioggia (mm/h)", 0, 50, 0)
k_diff = st.sidebar.slider("Diffusione Turbolenta (K)", 0.1, 2.5, 1.0)

# --- LOGICA DI CALCOLO ---
sigma_pioggia = (mm_pioggia / 50) * 0.3 

# --- CREAZIONE MAPPA DINAMICA ---
N = 50
dx, dt = 1.0, 0.02
edifici = np.zeros((N, N))
orografia = np.zeros((N, N))

np.random.seed(42)
if num_palazzi > 0:
    edifici[dist_primo_palazzo : dist_primo_palazzo+4, 23:27] = 1
    for _ in range(num_palazzi - 1):
        px, py = np.random.randint(15, 45), np.random.randint(10, 40)
        edifici[px:px+3, py:py+3] = 1

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

# --- MOTORE DI CALCOLO ADR ---
if st.sidebar.button("ESEGUI ANALISI METEOROLOGICA"):
    C = np.zeros((N, N))
    mappa_box = st.empty()
    testo_box = st.empty()
    sx, sy = 5, 25 

    for t in range(160):
        Cn = C.copy()
        Cn[sx, sy] += 160 * dt 
        
        for i in range(1, N-1):
            for j in range(1, N-1):
                if edifici[i,j] == 1: continue
                
                # Formula ADR
                diff = k_diff * dt * (C[i+1,j] + C[i-1,j] + C[i,j+1] + C[i,j-1] - 4*C[i,j])
                adv = -u_vento * dt * (C[i,j] - C[i-1,j])
                reac = -sigma_pioggia * dt * C[i,j]
                
                Cn[i,j] += diff + adv + reac

        C = np.where(edifici == 1, 0, Cn)
        C = np.clip(C, 0, 100)
        
        if t % 15 == 0:
            picco = np.max(C) * 0.15
            fig = go.Figure(data=[
                go.Surface(z=C + orografia, colorscale='Jet', cmin=0.01, cmax=12, name="Gas"),
                go.Surface(z=edifici * 4.5, colorscale='Greys', opacity=0.9, showscale=False),
                go.Surface(z=orografia, colorscale='Greens', opacity=0.3, showscale=False)
            ])
            
            fig.update_layout(
                scene=dict(zaxis=dict(range=[0, 15]), xaxis_title="X (m)", yaxis_title="Y (m)"),
                margin=dict(l=0, r=0, b=0, t=0), height=750
            )
            mappa_box.plotly_chart(fig, use
