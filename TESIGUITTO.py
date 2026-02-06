import streamlit as st
import numpy as np
import plotly.graph_objects as go

# Configurazione della pagina
st.set_page_config(page_title="Simulatore Dispersione Inquinanti", layout="wide")
st.title("Simulatore di Dispersione Inquinanti in Ambito Urbano")
st.write("Analisi della concentrazione basata sul modello Advezione-Diffusione-Reazione (ADR).")

# Menu laterale per i parametri di input
st.sidebar.header("Parametri di Simulazione")

# Definizione sostanze e relative soglie di allerta (ppm)
sostanza = st.sidebar.selectbox("Inquinante", ["Biossido di Azoto (NO2)", "Monossido di Carbonio (CO)", "Gas Tossico Industriale"])

if sostanza == "Biossido di Azoto (NO2)":
    soglia = 0.1
elif sostanza == "Monossido di Carbonio (CO)":
    soglia = 9.0
else:
    soglia = 0.05

# Parametri ambientali
u = st.sidebar.slider("Velocita del vento (u)", 0.1, 2.0, 0.5)
D = st.sidebar.slider("Coefficiente di Diffusione (K)", 0.5, 2.0, 1.2)
k_reac = 0.01 

# Parametri della sorgente di emissione
st.sidebar.subheader("Posizione Sorgente")
src_x = st.sidebar.slider("Coordinata X", 0, 49, 15)
src_y = st.sidebar.slider("Coordinata Y", 0, 49, 25)
q_rate = st.sidebar.slider("Portata emissione (Q)", 50, 200, 100)

# Impostazione della griglia numerica
nx, ny = 50, 50
dx = 1.0
dt = 0.02 # Passo temporale per stabilita numerica

# Definizione degli edifici (ostacoli fissi)
obstacles = np.zeros((nx, ny))
np.random.seed(42) # Seme fisso per riproducibilita dello scenario
for _ in range(12):
    ox, oy = np.random.randint(20, 45), np.random.randint(10, 40)
    obstacles[ox:ox+3, oy:oy+3] = 1

def esegui_simulazione():
    # Inizializzazione matrice concentrazione
    C = np.zeros((nx, ny))
    
    # Placeholder per aggiornamento grafico
    plot_area = st.empty()
    status_area = st.empty()
    
    # Ciclo di calcolo temporale
    for t in range(120):
        C_new = C.copy()
        
        # Aggiunta emissione alla sorgente
        C_new[src_x, src_y] += q_rate * dt
        
        # Risoluzione numerica dell'equazione ADR
        for i in range(1, nx-1):
            for j in range(1, ny-1):
                # Gestione presenza ostacoli
                if obstacles[i,j] == 1:
                    C_new[i,j] = 0
                    continue
                
                # Calcolo termine diffusivo (differenze centrali)
                diff = D * dt * (C[i+1,j] + C[i-1,j] + C[i,j+1] + C[i,j-1] - 4*C[i,j]) / (dx**2)
                
                # Calcolo termine advettivo (schema Upwind)
                adv = -u * dt * (C[i,j] - C[i-1,j]) / dx
                
                # Termine di decadimento
                reac = -k_reac * dt * C[i,j]
                
                C_new[i,j] += diff + adv + reac

        C = np.maximum(0, C_new) # Vincolo di positivita
        
        # Aggiornamento output grafico ogni 10 step
        if t % 10 == 0:
            # Calcolo del picco rilevato in prossimita degli edifici
            picco_rilevato = np.max(C[20:45, 10:40]) * 0.15 
            
            # Creazione superficie 3D
            fig = go.Figure(data=[
                go.Surface(z=C, colorscale='YlOrRd', name="Gas"),
                go.Surface(z=obstacles * 2, colorscale='Greys', opacity=0.5, showscale=False, name="Edifici")
            ])
            
            fig.update_layout(
                scene=dict(zaxis=dict(range=[0, 15])),
                margin=dict(l=0, r=0, b=0, t=0)
            )
            
            plot_area.plotly_chart(fig, use_container_width=True)
            
            # Logica di allerta
            if picco_rilevato > soglia:
                status_area.error(f"STATO: ALLERTA - Superamento soglia ({picco_rilevato:.3f} > {soglia})")
            else:
                status_area.success(f"STATO: SICURO - Sotto soglia ({picco_rilevato:.3f} < {soglia})")

# Bottone per avvio
if st.sidebar.button("Avvia Calcolo"):
    esegui_simulazione()
