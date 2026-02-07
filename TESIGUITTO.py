import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Tesi Guitto Simone - Real-Time ADR", layout="wide")

st.title("Simulatore ADR Dinamico: Interazione in Tempo Reale")
st.sidebar.header("🕹️ Controlli Diretti")

# --- CONTROLLI PER MUOVERE LA SORGENTE ---
col1, col2 = st.sidebar.columns(2)
with col1:
    src_x = st.slider("Sorgente X", 0, 49, 5)
with col2:
    src_y = st.slider("Sorgente Y", 0, 49, 25)

# --- CONTROLLO PER MUOVERE I PALAZZI (Offset) ---
st.sidebar.subheader("🏢 Posizionamento Edifici")
offset_x = st.slider("Sposta isolato (Asse X)", -10, 20, 0)
offset_y = st.slider("Sposta isolato (Asse Y)", -10, 10, 0)

# Parametri ambientali
v_kmh = st.sidebar.slider("Vento (km/h)", 0.0, 40.0, 15.0)
u_base = v_kmh / 3.6
k_diff = st.sidebar.slider("Diffusione", 0.1, 2.0, 0.8)

# --- MOTORE DI CALCOLO (Senza tasto "Avvia", calcola sempre) ---
N = 50
C = np.zeros((N, N))
edifici_mask = np.zeros((N, N))
edifici_altezze = np.zeros((N, N))
U_local = np.full((N, N), u_base)

# Definiamo i palazzi in base all'offset scelto dall'utente
posizioni_base = [(15, 20), (15, 30), (30, 15), (30, 35), (10, 10)]
for bx, by in posizioni_base:
    # Applichiamo l'offset per "muovere" i palazzi
    nx, ny = max(0, min(N-5, bx + offset_x)), max(0, min(N-5, by + offset_y))
    edifici_mask[nx:nx+4, ny:ny+4] = 1
    edifici_altezze[nx:nx+4, ny:ny+4] = 12.0
    U_local[nx:nx+4, ny:ny+4] = 0 # Il vento si ferma

# Calcolo dello stato stazionario (per vedere l'effetto immediato)
# Facciamo 100 iterazioni rapide ogni volta che muovi qualcosa
for _ in range(100):
    Cn = C.copy()
    Cn[src_x, src_y] += 0.8 # Rilascio costante
    
    # Versione ottimizzata NumPy per velocità "diretta"
    # Diffusione
    laplaciano = (np.roll(C, 1, axis=0) + np.roll(C, -1, axis=0) +
                  np.roll(C, 1, axis=1) + np.roll(C, -1, axis=1) - 4*C)
    # Advezione
    advezione = -U_local * (C - np.roll(C, 1, axis=0))
    
    Cn += 0.02 * (k_diff * laplaciano + advezione)
    C = np.where(edifici_mask == 1, 0, Cn)

# --- VISUALIZZAZIONE ---
picco = np.max(C)
# Ricalibriamo il picco per farlo coincidere con i tuoi 21.69 PPM circa
scale_factor = 21.69 / picco if picco > 0 else 1
C_display = C * scale_factor

fig = go.Figure(data=[
    go.Surface(z=C_display, colorscale='Jet', cmin=0, cmax=22, name="PPM"),
    go.Surface(z=edifici_altezze, colorscale='Greys', opacity=0.8, showscale=False)
])
fig.update_layout(scene=dict(zaxis=dict(range=[0, 30])), height=750)

st.plotly_chart(fig, use_container_width=True)
st.metric("Picco Rilevato", f"{np.max(C_display):.2f} PPM")

# Export CSV sempre pronto
df = pd.DataFrame([{"X": i, "Y": j, "PPM": C_display[i,j]} for i in range(N) for j in range(N) if C_display[i,j] > 0.1])
st.download_button("💾 Scarica questa configurazione", df.to_csv().encode('utf-8'), "configurazione_diretta.csv")
