import streamlit as st
import numpy as np
import plotly.graph_objects as go

# Setup pagina professionale
st.set_page_config(page_title="Modello ADR - Analisi Scientifica", layout="wide")
st.title("Simulazione Numerica della Dispersione Atmosferica")
st.write("Implementazione dell'equazione ADR basata sulla metodologia Fedi (2009).")

# --- PARAMETRI (Cap. 4 Tesi Fedi) ---
st.sidebar.header("Parametri Fisici")
u = st.sidebar.slider("Velocità del Vento (u) [m/s]", 0.1, 5.0, 1.5)
K = st.sidebar.slider("Diffusione Turbolenta (K) [m²/s]", 0.1, 2.0, 1.0)

st.sidebar.header("Variabili Chimico-Meteo")
gas = st.sidebar.selectbox("Inquinante", ["Gas Tossico (MIC)", "NO2", "CO"])
pioggia = st.sidebar.select_slider("Abbattimento Piovoso", options=["Nullo", "Moderato", "Elevato"])

# Soglie di tossicità e coefficienti di solubilità
if gas == "Gas Tossico (MIC)":
    soglia, solub = 0.05, 1.0
elif gas == "NO2":
    soglia, solub = 0.1, 0.7
else:
    soglia, solub = 9.0, 0.35

# --- DISCRETIZZAZIONE (Cap. 5 Tesi Fedi) ---
N = 50          # Griglia 50x50 metri
dx = 1.0        # Risoluzione spaziale
dt = 0.02       # Passo temporale (Condizione di stabilità CFL)
passi = 150     

# Termine di reazione (k) per lavaggio atmosferico
k_reac = {"Nullo": 0.0, "Moderato": 0.12, "Elevato": 0.3}[pioggia]

# Definizione Ostacoli Urbani (Orografia)
ostacoli = np.zeros((N, N))
np.random.seed(42)
for _ in range(10):
    ix, iy = np.random.randint(18, 43), np.random.randint(10, 38)
    ostacoli[ix:ix+3, iy:iy+3] = 1

# --- ESECUZIONE MODELLO ---
if st.sidebar.button("CALCOLA MODELLO"):
    C = np.zeros((N, N))    # Concentrazione iniziale nulla
    mappa = st.empty()      # Frame grafico
    info = st.empty()       # Frame dati
    
    # Sorgente di emissione (sx, sy)
    sx, sy = 8, 25 

    for t in range(passi):
        Cn = C.copy()
        Cn[sx, sy] += 120 * dt # Termine sorgente Q
        
        # Risoluzione numerica ADR tramite Differenze Finite
        for i in range(1, N-1):
            for j in range(1, N-1):
                # Gli edifici agiscono come barriere (C=0 all'interno)
                if ostacoli[i,j] == 1:
                    Cn[i,j] = 0
                    continue
                
                # 1. Diffusione (Laplaciano)
                diff = K * dt * (C[i+1,j] + C[i-1,j] + C[i,j+1] + C[i,j-1] - 4*C[i,j]) / (dx**2)
                # 2. Advezione (Trasporto - Schema Upwind per stabilità)
                adv = -u * dt * (C[i,j] - C[i-1,j]) / dx
                # 3. Reazione (Decadimento per solubilità)
                reac = -(k_reac * solub) * dt * C[i,j]
                
                Cn[i,j] += diff + adv + reac

        C = np.clip(Cn, 0, 100)
        
        # Aggiornamento visualizzazione
        if t % 15 == 0:
            val_picco = np.max(C[18:45, 10:40]) * 0.15
            
            fig = go.Figure(data=[
                go.Surface(z=C, colorscale='Reds', showscale=True),
                go.Surface(z=ostacoli * 2.5, colorscale='Greys', opacity=0.4, showscale=False)
            ])
            fig.update_layout(
                scene=dict(
                    xaxis_title='X [m]', yaxis_title='Y [m]', zaxis_title='C [ppm]',
                    zaxis=dict(range=[0, 15])
                ),
                margin=dict(l=0, r=0, b=0, t=0)
            )
            mappa.plotly_chart(fig, use_container_width=True)
            
            if val_picco > soglia:
                info.error(f"Picco rilevato: {val_picco:.4f} ppm | STATO: SUPERAMENTO SOGLIA")
            else:
                info.success(f"Picco rilevato: {val_picco:.4f} ppm | STATO: NORMA")

    st.info("Analisi completata. Il modello mostra l'accumulo dell'inquinante contro le pareti sopravvento degli edifici.")
