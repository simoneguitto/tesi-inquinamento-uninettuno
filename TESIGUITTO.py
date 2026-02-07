import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- INIZIALIZZAZIONE DEL SISTEMA ---
st.set_page_config(page_title="Simulatore ADR Urbano", layout="wide")
st.title("Modello Numerico di Dispersione degli Inquinanti")
st.write("Analisi della diffusione atmosferica tramite risoluzione numerica delle equazioni di trasporto.")

# --- DEFINIZIONE DEI PARAMETRI FISICI (SIDEBAR) ---
st.sidebar.header("Parametri di Controllo")
velocita_u = st.sidebar.slider("Velocità del fluido (u) [m/s]", 0.1, 5.0, 1.5)
diffusione_K = st.sidebar.slider("Coefficiente diffusivo (K) [m²/s]", 0.1, 2.0, 1.0)

st.sidebar.header("Variabili Ambientali")
sostanza_monitorata = st.sidebar.selectbox("Inquinante", ["Sostanza Alta Solubilità", "Sostanza Media Solubilità", "Sostanza Bassa Solubilità"])
intensita_pioggia = st.sidebar.select_slider("Grado di abbattimento", options=["Minimo", "Medio", "Massimo"])

# Parametri chimici e limiti di sicurezza
if sostanza_monitorata == "Sostanza Alta Solubilità":
    soglia_critica, sol_coeff = 0.05, 1.0
elif sostanza_monitorata == "Sostanza Media Solubilità":
    soglia_critica, sol_coeff = 0.1, 0.7
else:
    soglia_critica, sol_coeff = 9.0, 0.35

# --- DISCRETIZZAZIONE E DOMINIO COMPUTAZIONALE ---
dim_griglia = 50  # Nodi della griglia spaziale
dx = 1.0         # Risoluzione spaziale unitaria
dt = 0.02        # Intervallo temporale (rispetto della condizione di stabilità)
step_totali = 160 

# Coefficiente di rimozione per precipitazione
k_washout = {"Minimo": 0.0, "Medio": 0.12, "Massimo": 0.3}[intensita_pioggia]

# Configurazione della Topografia (Morfologia urbana)
# Gli ostacoli rappresentano volumi impermeabili che deviano il flusso
matrice_ostacoli = np.zeros((dim_griglia, dim_griglia))
np.random.seed(42)
for _ in range(10):
    ix, iy = np.random.randint(18, 43), np.random.randint(10, 38)
    matrice_ostacoli[ix:ix+3, iy:iy+3] = 1

# --- MOTORE DI CALCOLO (Metodo delle Differenze Finite) ---
if st.sidebar.button("ESEGUI SIMULAZIONE"):
    Conc = np.zeros((dim_griglia, dim_griglia)) # Matrice concentrazione tempo t
    area_grafica = st.empty()
    area_messaggi = st.empty()
    
    # Coordinate sorgente puntiforme
    p_x, p_y = 8, 25 

    for t in range(step_totali):
        Conc_n = Conc.copy()
        Conc_n[p_x, p_y] += 125 * dt # Termine sorgente (Emissione Q)
        
        # Iterazione spaziale per il calcolo dell'equazione ADR
        for i in range(1, dim_griglia-1):
            for j in range(1, dim_griglia-1):
                # Gestione dell'interazione con gli ostacoli orografici
                if matrice_ostacoli[i,j] == 1:
                    continue # Il volume solido non permette la penetrazione del gas
                
                # Calcolo componenti numeriche
                # 1. Diffusione (Operatore Laplaciano)
                term_diff = diffusione_K * dt * (Conc[i+1,j] + Conc[i-1,j] + Conc[i,j+1] + Conc[i,j-1] - 4*Conc[i,j]) / (dx**2)
                # 2. Trasporto Adveettivo (Direzione prevalente del vento - Schema Upwind)
                term_adv = -velocita_u * dt * (Conc[i,j] - Conc[i-1,j]) / dx
                # 3. Termine Reattivo (Rimozione fisica)
                term_reac = -(k_washout * sol_coeff) * dt * Conc[i,j]
                
                # Aggiornamento dello stato al passo temporale successivo
                Conc_n[i,j] += term_diff + term_adv + term_reac

        # Trattamento della Topografia: Mascheramento e aderenza alle pareti
        # Permette la visualizzazione della concentrazione a contatto con l'ostacolo
        Conc = np.where(matrice_ostacoli == 1, 0, Conc_n)
        Conc = np.clip(Conc, 0, 100) # Vincolo di massa non negativa
        
        # Rappresentazione visiva dei risultati (Mappatura 3D)
        if t % 15 == 0:
            picco_ppm = np.max(Conc[18:45, 10:40]) * 0.15
            
            figura = go.Figure(data=[
                go.Surface(z=Conc, colorscale='Reds', showscale=True, name="Gas"),
                go.Surface(z=matrice_ostacoli * 2.5, colorscale='Greys', opacity=0.4, showscale=False, name="Edifici")
            ])
            
            figura.update_layout(
                scene=dict(
                    xaxis_title='X [m]', yaxis_title='Y [m]', zaxis_title='C [ppm]',
                    zaxis=dict(range=[0, 15])
                ),
                margin=dict(l=0, r=0, b=0, t=0), height=650
            )
            area_grafica.plotly_chart(figura, use_container_width=True)
            
            # Valutazione del rischio in base alle soglie predefinite
            if picco_ppm > soglia_critica:
                area_messaggi.error(f"ATTENZIONE: Concentrazione massima {picco_ppm:.4f} ppm (Soglia superata)")
            else:
                area_messaggi.success(f"STATO: Concentrazione massima {picco_ppm:.4f} ppm (Entro i limiti)")

    st.info("Analisi conclusa. Il grafico illustra la variazione del pennacchio in funzione della topografia locale.")
