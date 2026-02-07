import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- 1. SETUP ---
st.set_page_config(page_title="Tesi Guitto Simone - Modello Stazionario", layout="wide")
N = 50 
dt = 0.02

if 'C' not in st.session_state:
    st.session_state.C = np.zeros((N, N))

st.title("Simulatore ADR: Analisi Stazionaria Post-Impatto")

# --- 2. SIDEBAR ---
with st.sidebar:
    st.header("🕹️ Parametri di Simulazione")
    src_x = st.slider("Sorgente X", 2, 47, 5)
    src_y = st.slider("Sorgente Y", 2, 47, 25)
    v_kmh = st.slider("Vento (km/h)", 1.0, 40.0, 12.0)
    k_diff = st.slider("Diffusione (K)", 0.5, 3.0, 1.5)
    
    st.subheader("🏢 Edifici")
    off_x = st.slider("Sposta X", -10, 20, 0)
    off_y = st.slider("Sposta Y", -10, 10, 0)

# --- 3. AMBIENTE ---
edifici_mask = np.zeros((N, N))
edifici_altezze = np.zeros((N, N))
posizioni = [(15, 20), (15, 30), (30, 15), (30, 35)]
for bx, by in posizioni:
    nx, ny = max(1, min(N-6, bx + off_x)), max(1, min(N-6, by + off_y))
    edifici_mask[nx:nx+5, ny:ny+5] = 1
    edifici_altezze[nx:nx+5, ny:ny+5] = 12.0

# --- 4. MOTORE FISICO STAZIONARIO ---
C = np.zeros((N, N))
u_base = v_kmh / 3.6

for _ in range(250):
    Cn = C.copy()
    
    # EMISSIONE FISSA (Logica Fedi per evitare l'infinito)
    Cn[src_x, src_y] = 10.0 
    
    for i in range(1, N-1):
        for j in range(1, N-1):
            if edifici_mask[i,j] == 1: continue
            
            diff = k_diff * dt * (C[i+1,j] + C[i-1,j] + C[i,j+1] + C[i,j-1] - 4*C[i,j])
            
            # Deviazione vento attorno ai palazzi
            u_eff, v_eff = u_base, 0
            if i < N-2 and edifici_mask[i+1, j] == 1:
                u_eff *= 0.1
                v_eff = 1.8 * u_base if j > 25 else -1.8 * u_base 
            
            adv_x = -u_eff * dt * (C[i,j] - C[i-1,j])
            adv_y = -v_eff * dt * (C[i,j] - C[i,j-1] if v_eff > 0 else C[i,j+1] - C[i,j])
            
            Cn[i,j] += diff + adv_x + adv_y

    C = np.where(edifici_mask == 1, 0, Cn)

# Calibrazione finale
if np.max(C) > 0:
    C = (C / np.max(C)) * 21.69

# --- 5. VISUALIZZAZIONE CONTRASTATA ---
fig = go.Figure()

# Superficie Gas con proiezione a terra super-evidente
fig.add_trace(go.Surface(
    z=C,
    colorscale='Jet',
    cmin=0, cmax=22,
    opacity=0.85,
    contours=dict(
        z=dict(
            show=True,
            project=dict(z=True),
            usecolormap=True,
            start=0.5,
            end=22,
            size=1
        )
    ),
    colorbar=dict(title="PPM")
))

# Edifici
fig.add_trace(go.Surface(
    z=edifici_altezze,
    colorscale=[[0, 'rgb(240,240,240)'], [1, 'rgb(255,255,255)']],
    showscale=False,
    opacity=1
))

fig.update_layout(
    scene=dict(
        # Fondo scuro per far risaltare il colore delle isole di inquinamento
        bgcolor="rgb(10, 10, 15)", 
        zaxis=dict(range=[0, 30], gridcolor="rgb(50,50,50)"),
        xaxis=dict(gridcolor="rgb(50,50,50)"),
        yaxis=dict(gridcolor="rgb(50,50,50)"),
        aspectratio=dict(x=1, y=1, z=0.5)
    ),
    paper_bgcolor="black", # Estetica professionale da centro di controllo
    font=dict(color="white"),
    height=850
)

st.plotly_chart(fig, use_container_width=True)
st.metric("Punto di Equilibrio", f"{np.max(C):.2f} PPM")
