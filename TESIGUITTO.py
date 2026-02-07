import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- CONFIGURAZIONE SISTEMA ---
st.set_page_config(page_title="Modello ADR Avanzato", layout="wide")
st.title("Simulazione di Dispersione Atmosferica e Analisi Ambientale")
st.write("Studio dell'evoluzione spazio-temporale di inquinanti in funzione delle variabili meteorologiche.")

# --- INPUT: CONDIZIONI ATMOSFERICHE (SIDEBAR) ---
st.sidebar.header("Condizioni Atmosferiche")
# La stabilità influenza la diffusione (K) e il trasporto (u)
stabilita = st.sidebar.selectbox("Stabilità Atmosferica", ["Instabile (Giorno)", "Neutra", "Stabile (Inversione Notturna)"])

# Parametri dinamici basati sulla stabilità
if stabilita == "Instabile (Giorno)":
    u_def, k_def = 1.0, 1.8  # Molta diffusione, vento moderato
elif stabilita == "Neutra":
    u_def, k_def = 1.5, 1.0  # Condizioni standard
else:
    u_def, k_def = 0.5, 0.2  # Aria ferma, ristagno massimo (Pericolo elevato)

u_vento = st.sidebar.slider("Velocità del Vento (u) [m/s]", 0.1, 5.0, u_def)
k_diff = st.sidebar.slider("Coefficiente di Diffusione (K)", 0.1, 2.5, k_def)

st.sidebar.header("Parametri di Abbattimento (Pioggia)")
pioggia = st.sidebar.select_slider("Grado di Piovosità", options=["Zero", "Leggera", "Forte"])
sostanza = st.sidebar.selectbox("Tipo Inquinante", ["Altamente Solubile", "Mediamente Solubile", "Poco Solubile"])

# Definizione fisica del lavaggio atmosferico (Scavenging Coefficient)
if sostanza == "Altamente Solubile":
    soglia, sol_index = 0.05, 1.0
elif sostanza == "Mediamente Solubile":
    soglia, sol_index = 0.1, 0.7
else:
    soglia, sol_index = 9.0, 0.3

# --- DISCRETIZZAZIONE NUMERICA ---
N = 50
dx = 1.0
dt = 0.02
step = 160

# Calcolo del termine di reazione (sigma) per la pioggia
# Pioggia * Solubilità = Quanto gas viene rimosso dall'aria
sigma_base = {"Zero": 0.0, "Leggera": 0.1, "Forte": 0.25}[pioggia]
sigma_reale = sigma_base * sol_index

# Topografia (Edifici)
ostacoli = np.zeros((N, N))
np.random.seed(42)
for _ in range(10):
    ix, iy = np.random.randint(18, 43), np.random.randint(10, 38)
    ostacoli[ix:ix+3, iy:iy+3] = 1

# --- ESECUZIONE CALCOLO ---
if st.sidebar.button("ANALIZZA DISPERSIONE"):
    C = np.zeros((N, N))
    mappa = st.empty()
    status = st.empty()
    
    source_x, source_y = 8, 25 

    for t in range(step):
        Cn = C.copy()
        Cn[source_x, source_y] += 130 * dt # Emissione sorgente
        
        for i in range(1, N-1):
            for j in range(1, N-1):
                if ostacoli[i,j] == 1:
                    continue
                
                # EQUAZIONE ADR: Advezione + Diffusione - Reazione (Pioggia)
                # 1. Diffusione (Allargamento della nuvola)
                diff = k_diff * dt * (C[i+1,j] + C[i-1,j] + C[i,j+1] + C[i,j-1] - 4*C[i,j])
                # 2. Advezione (Trasporto del vento)
                adv = -u_vento * dt * (C[i,j] - C[i-1,j])
                # 3. Reazione (Lavaggio piovoso)
                reac = -sigma_reale * dt * C[i,j]
                
                Cn[i,j] += diff + adv + reac

        # Topografia: eliminazione del vuoto visivo (mascheramento post-computazione)
        C = np.where(ostacoli == 1, 0, Cn)
        C = np.clip(C, 0, 100)
        
        if t % 15 == 0:
            picco = np.max(C[15:45, 10:40]) * 0.15
            
            fig = go.Figure(data=[
                go.Surface(z=C, colorscale='YlOrRd', showscale=True),
                go.Surface(z=ostacoli * 2.5, colorscale='Greys', opacity=0.5, showscale=False)
            ])
            
            fig.update_layout(
                scene=dict(zaxis=dict(range=[0, 15]), xaxis_title='X', yaxis_title='Y', zaxis_title='ppm'),
                margin=dict(l=0, r=0, b=0, t=0)
            )
            mappa.plotly_chart(fig, use_container_width=True)
            
            if picco > soglia:
                status.error(f"LIVELLO CRITICO: {picco:.4f} ppm - Soglia superata")
            else:
                status.success(f"LIVELLO SICURO: {picco:.4f} ppm")

    st.info("Simulazione terminata. Il modello evidenzia come la pioggia riduca la portata del pennacchio mentre la stabilità atmosferica ne definisce l'ampiezza.")
