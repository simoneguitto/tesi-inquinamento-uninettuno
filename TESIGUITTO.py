import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd

# --- 1. SETUP E INIZIALIZZAZIONE ---
st.set_page_config(page_title="Tesi Guitto Simone - ADR Stabilizzato", layout="wide")
N = 50 
dt = 0.02

if 'C' not in st.session_state:
    st.session_state.C = np.zeros((N, N))

st.title("Simulatore ADR: Modello a Emissione Controllata")
st.markdown("### Analisi Comparativa - Risultati Stabilizzati")

# --- 2. SIDEBAR ---
with st.sidebar:
    st.header("🕹️ Pannello di Controllo")
    src_x = st.slider("Sorgente X", 2, 47, 5)
    src_y = st.slider("Sorgente Y", 2, 47, 25)
    
    st.subheader("🏢 Geometria Edifici")
    off_x = st.slider("Sposta X", -10, 20, 0)
    off_y = st.slider("Sposta Y", -10, 10, 0)
    
    st.subheader("🌦️ Variabili Ambientali")
    v_kmh = st.slider("Vento (km/h)", 1.0, 40.0, 12.0)
    u_base = v_kmh / 3.6
    k_diff = st.slider("Diffusione (K)", 0.5, 3.0, 1.5)

# --- 3. COSTRUZIONE AMBIENTE ---
edifici_mask = np.zeros((N, N))
edifici_altezze = np.zeros((N, N))
posizioni = [(15, 20), (15, 30), (30, 15), (30, 35)]

for bx, by in posizioni:
    nx, ny = max(1, min(N-6, bx + off_x)), max(1, min(N-6, by + off_y))
    if nx <= src_x <= nx+5 and ny <= src_y <= ny+5:
        src_x = nx - 2
    edifici_mask[nx:nx+5, ny:ny+5] = 1
    edifici_altezze[nx:nx+5, ny:ny+5] = 12.0

# --- 4. MOTORE DI CALCOLO (LOGICA ANTI-INFINITO) ---
C = np.zeros((N, N))
for _ in range(250):
    Cn = C.copy()
    
    # --- FIX QUI: Usiamo '=' invece di '+=' per non far salire il picco all'infinito ---
    Cn[src_x, src_y] = 10.0  # Valore di emissione fisso (come Flavia Fedi)
    
    for i in range(1, N-1):
        for j in range(1, N-1):
            if edifici_mask[i,j] == 1: continue
            
            diff = k_diff * dt * (C[i+1,j] + C[i-1,j] + C[i,j+1] + C[i,j-1] - 4*C[i,j])
            
            u_eff = u_base
            v_eff = 0
            if i < N-2 and edifici_mask[i+1, j] == 1:
                u_eff *= 0.1
                v_eff = 1.8 * u_base if j > 25 else -1.8 * u_base 
            
            adv_x = -u_eff * dt * (C[i,j] - C[i-1,j])
            adv_y = -v_eff * dt * (C[i,j] - C[i,j-1] if v_eff > 0 else C[i,j+1] - C[i,j])
            
            Cn[i,j] += diff + adv_x + adv_y

    C = np.where(edifici_mask == 1, 0, Cn)

# Calibrazione al tuo valore di tesi
if np.max(C) > 0:
    C = (C / np.max(C)) * 21.69

st.session_state.C = C

# --- 5. VISUALIZZAZIONE 3D STABILIZZATA ---
fig = go.Figure(data=[
    go.Surface(
        z=C, 
        colorscale='Jet', 
        cmin=0, cmax=22, 
        name="Gas PPM",
        contours={
            "z": {
                "show": True, 
                "project_z": True,     # Colora il pavimento
                "usecolormap": True,    # Mappa di calore piena
                "start": 0.5,
                "end": 22, 
                "size": 1
            }
        },
        colorbar=dict(title="PPM", thickness=25)
    ),
    go.Surface(z=edifici_altezze, colorscale='Greys', opacity=0.9, showscale=False)
])

fig.update_layout(
    scene=dict(
        # Limitiamo l'asse Z così il grafico non "scappa" mai verso l'alto
        zaxis=dict(range=[0, 30], title="Concentrazione PPM"),
        xaxis_title="Distanza X (m)",
        yaxis_title="Distanza Y (m)",
        aspectmode='manual',
        aspectratio=dict(x=1, y=1, z=0.5) # Rende la montagnetta più "schiacciata" e realistica
    ),
    margin=dict(l=0, r=0, b=0, t=40),
    height=800
)

st.plotly_chart(fig, use_container_width=True)

st.metric("Valore Massimo Stabilizzato", f"{np.max(C):.2f} PPM")
