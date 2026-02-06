import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Simulatore Dispersione", layout="wide")
st.title("Simulatore di Dispersione Inquinanti: Analisi Meteorologica")

# --- PARAMETRI METEOROLOGICI E AMBIENTALI ---
st.sidebar.header("Condizioni Meteorologiche")

# La stabilita atmosferica determina quanto il gas si allarga (Diffusione)
stabilita = st.sidebar.selectbox(
    "Stabilità Atmosferica (Pasquill)",
    ["Instabile (Forte turbolenza)", "Neutra (Vento moderato)", "Stabile (Inversione termica)"]
)

# Impostazione automatica del coefficiente D in base alla stabilita scelta
if stabilita == "Instabile (Forte turbolenza)":
    D_default = 1.8
    u_default = 0.5
    desc_meteo = "Condizioni di forte rimescolamento (giornata soleggiata)."
elif stabilita == "Neutra (Vento moderato)":
    D_default = 1.0
    u_default = 1.2
    desc_meteo = "Condizioni medie (cielo coperto o vento costante)."
else:
    D_default = 0.3
    u_default = 0.2
    desc_meteo = "Rischio ristagno elevato (notte o inversione termica)."

u = st.sidebar.slider("Velocita del vento (u) [m/s]", 0.1, 5.0, u_default)
D = st.sidebar.slider("Coefficiente di Diffusione (K)", 0.1, 2.5, D_default)

st.sidebar.info(desc_meteo)

# --- PARAMETRI CHIMICI E SORGENTE ---
st.sidebar.header("Parametri Sorgente")
sostanza = st.sidebar.selectbox("Inquinante", ["Biossido di Azoto (NO2)", "Monossido di Carbonio (CO)", "Gas Tossico"])
soglia = 0.1 if sostanza == "Biossido di Azoto (NO2)" else 9.0 if sostanza == "Monossido di Carbonio (CO)" else 0.05

src_x = st.sidebar.slider("Posizione X Sorgente", 0, 49, 10)
src_y = st.sidebar.slider("Posizione Y Sorgente", 0, 49, 25)
q_rate = st.sidebar.number_input("Portata Sorgente (Q)", 10.0, 500.0, 100.0)

# --- GRIGLIA E CALCOLO ---
nx, ny = 50, 50
dx = 1.0
dt = 0.02 
k_reac = 0.01

# Definizione ostacoli urbani
obstacles = np.zeros((nx, ny))
np.random.seed(42)
for _ in range(12):
    ox, oy = np.random.randint(20, 45), np.random.randint(10, 40)
    obstacles[ox:ox+3, oy:oy+3] = 1

def calcola_dispersione():
    C = np.zeros((nx, ny))
    grafico = st.empty()
    testo_stato = st.empty()
    
    for t in range(150):
        C_new = C.copy()
        C_new[src_x, src_y] += q_rate * dt
        
        # Algoritmo di risoluzione equazione ADR
        for i in range(1, nx-1):
            for j in range(1, ny-1):
                if obstacles[i,j] == 1:
                    C_new[i,j] = 0
                    continue
                
                # Diffusione (Laplaciano)
                diff = D * dt * (C[i+1,j] + C[i-1,j] + C[i,j+1] + C[i,j-1] - 4*C[i,j]) / (dx**2)
                # Advezione (Schema Upwind - Trasporto del vento)
                adv = -u * dt * (C[i,j] - C[i-1,j]) / dx
                # Reazione (Decadimento)
                reac = -k_reac * dt * C[i,j]
                
                C_new[i,j] += diff + adv + reac

        C = np.maximum(0, C_new)
        
        if t % 15 == 0:
            picco = np.max(C[obstacles == 1 + 1] if np.any(obstacles) else 0)
            val_riferimento = np.max(C[20:45, 10:40]) * 0.12
            
            fig = go.Figure(data=[
                go.Surface(z=C, colorscale='YlOrRd'),
                go.Surface(z=obstacles * 1.5, colorscale='Greys', opacity=0.4, showscale=False)
            ])
            fig.update_layout(scene=dict(zaxis=dict(range=[0, 10])), margin=dict(l=0, r=0, b=0, t=0))
            grafico.plotly_chart(fig, use_container_width=True)
            
            if val_riferimento > soglia:
                testo_stato.error(f"Soglia superata sui palazzi: {val_riferimento:.3f} ppm")
            else:
                testo_stato.success(f"Livelli di sicurezza rispettati: {val_riferimento:.3f} ppm")

if st.sidebar.button("Esegui Analisi"):
    calcola_dispersione()
