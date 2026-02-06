import streamlit as st
import numpy as np
import plotly.graph_objects as go

# Configurazione interfaccia
st.set_page_config(page_title="Modello ADR - Tesi", layout="wide")
st.title("Simulazione Numerica della Dispersione Atmosferica")
st.write("Modello basato sulle equazioni di Flavia Fedi (2009) con varianti urbanistiche.")

# --- INPUT (Logica Capitolo 4: Formulazione del Modello) ---
st.sidebar.header("Parametri Fisici")
u = st.sidebar.slider("Velocità del Vento (u) [m/s]", 0.1, 5.0, 1.5)
K = st.sidebar.slider("Coefficiente di Diffusione (K) [m²/s]", 0.1, 2.0, 1.0)

st.sidebar.header("Chimica e Meteo")
gas = st.sidebar.selectbox("Inquinante", ["Gas Tossico (MIC)", "NO2", "CO"])
pioggia = st.sidebar.select_slider("Abbattimento (Pioggia)", options=["Nullo", "Medio", "Forte"])

# Parametri di soglia e solubilità
if gas == "Gas Tossico (MIC)": soglia, solub = 0.05, 1.0
elif gas == "NO2": soglia, solub = 0.1, 0.7
else: soglia, solub = 9.0, 0.3

# --- DISCRETIZZAZIONE (Logica Capitolo 5: Soluzione Numerica) ---
N = 50          # Numero nodi griglia
dx = 1.0        # Passo spaziale (1 metro)
dt = 0.02       # Passo temporale (piccolo per stabilità)
passi = 150     # Numero di iterazioni temporali

# Coefficiente di decadimento per pioggia (Termine di Reazione)
k_reac = {"Nullo": 0.0, "Medio": 0.12, "Forte": 0.3}[pioggia]

# Mappa degli Edifici (Tua modifica rispetto alla tesi originale)
edifici = np.zeros((N, N))
np.random.seed(42)
for _ in range(10):
    ix, iy = np.random.randint(15, 42), np.random.randint(10, 38)
    edifici[ix:ix+3, iy:iy+3] = 1

# --- ESECUZIONE (Logica Capitolo 6: Risultati) ---
if st.button("ESEGUI SIMULAZIONE"):
    C = np.zeros((N, N))    # Matrice concentrazione iniziale
    mappa = st.empty()      # Contenitore per il grafico
    info = st.empty()       # Contenitore per i dati
    
    # Sorgente puntiforme (Ciminiera)
    sx, sy = 5, 25 

    for t in range(passi):
        Cn = C.copy()
        Cn[sx, sy] += 120 * dt # Rilascio costante Q
        
        # Calcolo numerico ADR
        for i in range(1, N-1):
            for j in range(1, N-1):
                # Se c'è un palazzo, la concentrazione è zero (Gas non penetra)
                if edifici[i,j] == 1:
                    Cn[i,j] = 0
                    continue
                
                # EQUAZIONE DI FEDI (Discretizzata)
                # 1. Diffusione (Laplaciano)
                diff = K * dt * (C[i+1,j] + C[i-1,j] + C[i,j+1] + C[i,j-1] - 4*C[i,j]) / (dx**2)
                # 2. Advezione (Trasporto del vento - Schema Upwind)
                adv = -u * dt * (C[i,j] - C[i-1,j]) / dx
                # 3. Reazione (Abbattimento pioggia)
                reac = -(k_reac * solub) * dt * C[i,j]
                
                Cn[i,j] += diff + adv + reac

        C = np.clip(Cn, 0, 100)
        
        # Aggiornamento grafico ogni 15 step
        if t % 15 == 0:
            picco_attuale = np.max(C[15:45, 10:40]) * 0.15
            
            fig = go.Figure(data=[
                go.Surface(z=C, colorscale='Reds', name="Gas"),
                go.Surface(z=edifici * 3, colorscale='Greys', opacity=0.5, showscale=False)
            ])
            fig.update_layout(scene=dict(zaxis=dict(range=[0, 15])), margin=dict(l=0, r=0, b=0, t=0))
            mappa.plotly_chart(fig, use_container_width=True)
            
            if picco_attuale > soglia:
                info.error(f"Picco rilevato: {picco_attuale:.4f} ppm | SOGLIA SUPERATA")
            else:
                info.success(f"Picco rilevato: {picco_attuale:.4f} ppm | LIVELLI SICURI")

    st.balloons()
