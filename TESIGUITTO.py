import streamlit as st
import numpy as np
import plotly.graph_objects as go

# Configurazione interfaccia
st.set_page_config(page_title="Simulatore ADR - Urban Air Quality", layout="wide")
st.title("Modellazione Numerica della Dispersione Atmosferica")
st.write("Evoluzione dinamica del modello Advezione-Diffusione-Reazione per la valutazione del rischio urbano.")

# --- SIDEBAR: CONFIGURAZIONE SCENARIO ---
st.sidebar.header("Variabili Ambientali")

# Stabilità atmosferica (Parametro chiave per la diffusione)
meteo = st.sidebar.selectbox(
    "Stabilità Atmosferica", 
    ["Instabile (Forte Rimescolamento)", "Neutra", "Stabile (Inversione Termica)"]
)

# Gestione Pioggia (Miglioramento del modello di rimozione inquinanti)
pioggia = st.sidebar.select_slider(
    "Intensità Precipitazioni",
    options=["Nessuna", "Leggera", "Moderata", "Forte"]
)

# Definizione parametri fisici
if meteo == "Instabile (Forte Rimescolamento)":
    D_val, u_val = 1.7, 0.7
elif meteo == "Neutra":
    D_val, u_val = 1.0, 1.5
else:
    D_val, u_val = 0.2, 0.3

# Coefficiente di 'Wash-out' (Lavaggio atmosferico)
scavenging_rates = {"Nessuna": 0.01, "Leggera": 0.08, "Moderata": 0.18, "Forte": 0.35}
k_reac = scavenging_rates[pioggia]

u = st.sidebar.slider("Velocità del Vento (u) [m/s]", 0.1, 5.0, u_val)
D = st.sidebar.slider("Coefficiente di Diffusione (K)", 0.1, 2.5, D_val)

# --- SORGENTE E SOSTANZA ---
st.sidebar.header("Parametri Chimici")
sostanza = st.sidebar.selectbox("Tipo di Gas", ["Tossico Industriale", "Biossido di Azoto", "Monossido di Carbonio"])

# Soglie di rischio (Rif. limiti di esposizione acuta)
if sostanza == "Tossico Industriale":
    soglia = 0.05
elif sostanza == "Biossido di Azoto":
    soglia = 0.1
else:
    soglia = 9.0

q_rate = st.sidebar.slider("Emissione alla Sorgente (Q)", 50, 250, 120)

# --- MOTORE DI CALCOLO (Differenze Finite) ---
nx, ny = 50, 50
dx = 1.0

# Calcolo dt dinamico per evitare instabilità (CFL Condition)
dt = 0.4 * (dx / (u + D + 0.1))
if dt > 0.05: dt = 0.05

# Mappa Edifici (Orografia Urbana)
obstacles = np.zeros((nx, ny))
np.random.seed(42)
for _ in range(12):
    ox, oy = np.random.randint(18, 45), np.random.randint(10, 40)
    obstacles[ox:ox+3, oy:oy+3] = 1

def simula_processo():
    C = np.zeros((nx, ny))
    grafico = st.empty()
    alert = st.empty()
    
    # Coordinate sorgente
    sx, sy = 10, 25

    for t in range(140):
        C_new = C.copy()
        C_new[sx, sy] += q_rate * dt
        
        # Algoritmo ADR (Advezione-Diffusione-Reazione)
        for i in range(1, nx-1):
            for j in range(1, ny-1):
                if obstacles[i,j] == 1:
                    C_new[i,j] = 0
                    continue
                
                # Calcolo variazione spaziale
                diff = D * dt * (C[i+1,j] + C[i-1,j] + C[i,j+1] + C[i,j-1] - 4*C[i,j])
                adv = -u * dt * (C[i,j] - C[i-1,j]) # Schema Upwind per stabilità
                reac = -k_reac * dt * C[i,j] # Effetto pioggia/decadimento
                
                C_new[i,j] += diff + adv + reac

        C = np.clip(C_new, 0, 50) # Protezione valori fisici
        
        if t % 14 == 0:
            # Rilevamento impatto sulle facciate
            picco_rilevato = np.max(C[20:45, 10:40]) * 0.14
            
            fig = go.Figure(data=[
                go.Surface(z=C, colorscale='Hot', showscale=True),
                go.Surface(z=obstacles * 2, colorscale='Greys', opacity=0.5, showscale=False)
            ])
            fig.update_layout(scene=dict(zaxis=dict(range=[0, 15])), margin=dict(l=0, r=0, b=0, t=0))
            grafico.plotly_chart(fig, use_container_width=True)
            
            if picco_rilevato > soglia:
                alert.error(f"ATTENZIONE: SUPERAMENTO SOGLIA | Valore: {picco_rilevato:.3f} ppm | Limite: {soglia}")
            else:
                alert.success(f"SICURO: LIVELLI CONTROLLATI | Valore: {picco_rilevato:.3f} ppm | Limite: {soglia}")

if st.sidebar.button("Avvia Modello Numerico"):
    simula_processo()
