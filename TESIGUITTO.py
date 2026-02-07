import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="Tesi Guitto Simone - Fix Stabilità", layout="wide")
N = 50
dt = 0.02

if 'C' not in st.session_state:
    st.session_state.C = np.zeros((N, N))

st.title("Simulatore ADR: Stabilità Coordinate e Mappatura Rischio")

# --- 2. SIDEBAR ---
with st.sidebar:
    st.header("🕹️ Posizionamento")
    # Limito il range della sorgente per non farla finire "dentro" i bordi
    src_x = st.slider("Sorgente X", 2, 47, 5)
    src_y = st.slider("Sorgente Y", 2, 47, 25)
    
    st.subheader("🏢 Configurazione Edifici")
    off_x = st.slider("Sposta X", -10, 20, 0)
    off_y = st.slider("Sposta Y", -10, 10, 0)
    
    v_kmh = st.slider("Vento (km/h)", 1.0, 40.0, 12.0)
    u_base = v_kmh / 3.6
    k_diff = st.slider("Diffusione (K)", 0.5, 3.0, 1.2)

# --- 3. COSTRUZIONE AMBIENTE ---
edifici_mask = np.zeros((N, N))
edifici_altezze = np.zeros((N, N))
posizioni = [(15, 20), (15, 30), (30, 15), (30, 35)]

for bx, by in posizioni:
    nx, ny = max(1, min(N-6, bx + off_x)), max(1, min(N-6, by + off_y))
    # Se la sorgente è dentro l'area del palazzo, la "spingiamo" fuori
    if nx <= src_x <= nx+5 and ny <= src_y <= ny+5:
        src_x = nx - 2 # Sposta la sorgente per non farla sparire
    
    edifici_mask[nx:nx+5, ny:ny+5] = 1
    edifici_altezze[nx:nx+5, ny:ny+5] = 12.0

# --- 4. MOTORE DI CALCOLO ---
C = np.zeros((N, N))
for _ in range(200):
    Cn = C.copy()
    Cn[src_x, src_y] += 2.5 # Sorgente rinforzata per visibilità
    
    for i in range(1, N-1):
        for j in range(1, N-1):
            if edifici_mask[i,j] == 1: continue
            
            diff = k_diff * dt * (C[i+1,j] + C[i-1,j] + C[i,j+1] + C[i,j-1] - 4*C[i,j])
            
            u_eff = u_base
            v_eff = 0
            if i < N-2 and edifici_mask[i+1, j] == 1:
                u_eff *= 0.1
                v_eff = 1.5 * u_base if j > 25 else -1.5 * u_base 
            
            Cn[i,j] += diff - u_eff * dt * (C[i,j] - C[i-1,j]) - v_eff * dt * (C[i,j] - C[i,j-1] if v_eff > 0 else C[i,j+1] - C[i,j])

    C = np.where(edifici_mask == 1, 0, Cn)

if np.max(C) > 0:
    C = (C / np.max(C)) * 21.69

# --- 5. VISUALIZZAZIONE (FIX DEI PALAZZI CHE SI ALZANO) ---
fig = go.Figure(data=[
    go.Surface(
        z=C, colorscale='Jet', cmin=0, cmax=22, name="PPM",
        contours={"z": {"show": True, "project_z": True, "usecolormap": True, "start": 0.5}}
    ),
    go.Surface(z=edifici_altezze, colorscale='Greys', opacity=0.9, showscale=False)
])

fig.update_layout(
    scene=dict(
        # BLOCCHIAMO IL RANGE Z: così i palazzi non cambiano altezza visiva
        zaxis=dict(range=[0, 30], title="PPM / Altezza"),
        xaxis=dict(range=[0, 50]),
        yaxis=dict(range=[0, 50]),
        aspectmode='cube' # Mantiene le proporzioni costanti
    ),
    height=800
)

st.plotly_chart(fig, use_container_width=True)
st.metric("Valore Sperimentale", f"{np.max(C):.2f} PPM")
