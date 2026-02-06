import streamlit as st
import numpy as np
import plotly.graph_objects as go

# Configurazione semplice
st.set_page_config(page_title="Simulatore Inquinamento Urbano", layout="wide")
st.title("Studio della Dispersione Inquinanti in Area Urbana")

# --- SEZIONE METEOROLOGIA (Fondamentale per la tesi) ---
st.sidebar.header("Condizioni Meteo")

# Selettore per la stabilita dell'aria (Classi di Pasquill semplificate)
meteo = st.sidebar.selectbox(
    "Stato dell'Atmosfera", 
    ["Giorno Soleggiato (Instabile)", "Cielo Coperto (Neutro)", "Notte/Inversione (Stabile)"]
)

# Impostazione dei parametri fisici in base al meteo
if meteo == "Giorno Soleggiato (Instabile)":
    D_base = 1.8  # Molta dispersione
    u_base = 1.0
    nota = "L'aria calda sale: l'inquinante si disperde velocemente."
elif meteo == "Cielo Coperto (Neutro)":
    D_base = 1.0
    u_base = 2.0
    nota = "Condizioni medie di dispersione."
else:
    D_base = 0.2  # Ristagno critico
    u_base = 0.3
    nota = "Inversione termica: l'inquinante resta schiacciato a terra."

# Slider per personalizzare i valori
u = st.sidebar.slider("Velocità Vento (u) [m/s]", 0.1, 4.0, u_base)
D = st.sidebar.slider("Diffusione (K)", 0.1, 2.5, D_base)
st.sidebar.caption(nota)

# --- PARAMETRI SORGENTE E INQUINANTE ---
st.sidebar.header("Parametri Sorgente")
inquinante = st.sidebar.selectbox("Sostanza", ["NO2", "CO", "Gas Tossico"])
soglia = 0.1 if inquinante == "NO2" else 9.0 if inquinante == "CO" else 0.05

q_rate = st.sidebar.slider("Quantità emessa (Q)", 50, 200, 100)

# --- CALCOLO NUMERICO ---
nx, ny = 50, 50
dx = 1.0

# Calcolo automatico del passo temporale (dt) per evitare numeri impazziti (CFL)
dt = 0.4 * (dx / (u + D + 0.1)) 
if dt > 0.05: dt = 0.05

# Creazione edifici fissi
obstacles = np.zeros((nx, ny))
np.random.seed(42)
for _ in range(12):
    ox, oy = np.random.randint(20, 45), np.random.randint(10, 40)
    obstacles[ox:ox+3, oy:oy+3] = 1

def start_sim():
    C = np.zeros((nx, ny))
    plot = st.empty()
    txt = st.empty()
    
    # Punto di rilascio
    sx, sy = 10, 25

    for t in range(120):
        C_new = C.copy()
        C_new[sx, sy] += q_rate * dt
        
        # Formule di trasporto (Advezione + Diffusione)
        for i in range(1, nx-1):
            for j in range(1, ny-1):
                if obstacles[i,j] == 1:
                    C_new[i,j] = 0
                    continue
                
                # Calcolo della variazione (Schema Upwind e Laplaciano)
                diff = D * dt * (C[i+1,j] + C[i-1,j] + C[i,j+1] + C[i,j-1] - 4*C[i,j])
                adv = -u * dt * (C[i,j] - C[i-1,j])
                
                C_new[i,j] += diff + adv
        
        # Limitatore di sicurezza per numeri realistici
        C = np.clip(C_new, 0, 50)
        
        if t % 12 == 0:
            # Calcolo del picco sui palazzi con scala realistica
            val_palazzi = np.max(C[20:45, 10:40]) * 0.15 
            
            fig = go.Figure(data=[
                go.Surface(z=C, colorscale='YlOrRd', showscale=False),
                go.Surface(z=obstacles * 2, colorscale='Greys', opacity=0.4, showscale=False)
            ])
            fig.update_layout(scene=dict(zaxis=dict(range=[0, 10])), margin=dict(l=0, r=0, b=0, t=0))
            plot.plotly_chart(fig, use_container_width=True)
            
            res = "ALLERTA" if val_palazzi > soglia else "SICURO"
            txt.write(f"Stato: {res} | Picco su Edifici: {val_palazzi:.3f} ppm | Soglia: {soglia}")

if st.sidebar.button("Avvia Simulazione"):
    start_sim()
