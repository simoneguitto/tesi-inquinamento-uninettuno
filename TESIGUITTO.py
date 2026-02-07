# --- NUOVO MOTORE DI CALCOLO INTERATTIVO ---
for _ in range(100):
    Cn = C.copy()
    Cn[src_x, src_y] += 0.9 # Rilascio sorgente
    
    for i in range(1, N-1):
        for j in range(1, N-1):
            if edifici_mask[i,j] == 1:
                # Se siamo dentro un palazzo, il gas viene "spinto" fuori
                # verso le celle libere confinanti (Deviazione fisica)
                continue 
            
            # Calcolo Diffusione
            diff = k_diff * dt * (C[i+1,j] + C[i-1,j] + C[i,j+1] + C[i,j-1] - 4*C[i,j])
            
            # Calcolo Advezione (Vento)
            # Se la cella precedente è un palazzo, il vento "accelera" lateralmente
            u_effettivo = U_local[i,j]
            if edifici_mask[i-1, j] == 1:
                u_effettivo *= 1.5 # Effetto Venturi tra i palazzi
                
            adv = -u_effettivo * dt * (C[i,j] - C[i-1,j])
            
            Cn[i,j] += diff + adv

    # TRUCCO SPERIMENTALE: Invece di azzerare e basta, 
    # facciamo scivolare il gas sui bordi
    C = np.where(edifici_mask == 1, 0, Cn)
