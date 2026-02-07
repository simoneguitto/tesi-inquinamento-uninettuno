# --- MOTORE DI CALCOLO "MODELLO FEDI" (AGGIRAMENTO) ---
for _ in range(120):
    Cn = C.copy()
    Cn[src_x, src_y] += 1.2 # Sorgente
    
    for i in range(1, N-1):
        for j in range(1, N-1):
            if edifici_mask[i,j] == 1:
                continue
            
            # --- LOGICA DI AGGIRAMENTO ---
            # Se la cella accanto è un palazzo, la diffusione non entra nel palazzo 
            # ma viene "respinta" nelle celle libere (No-Flux)
            diff_x = k_diff * dt * (C[i+1,j] + C[i-1,j] - 2*C[i,j])
            diff_y = k_diff * dt * (C[i,j+1] + C[i,j-1] - 2*C[i,j])
            
            # Se davanti (asse X) c'è un palazzo, il vento deve deviare lateralmente (asse Y)
            u_eff = u_base
            v_side = 0
            if edifici_mask[i+1, j] == 1:
                u_eff = u_base * 0.1 # Il vento rallenta contro il muro
                v_side = u_base * 0.4 # Il gas viene spinto di lato per aggirare
                
            adv_x = -u_eff * dt * (C[i,j] - C[i-1,j])
            adv_y = -v_side * dt * (C[i,j] - C[i,j-1]) # Questa è la chiave dell'aggiramento
            
            Cn[i,j] += diff_x + diff_y + adv_x + adv_y

    C = np.where(edifici_mask == 1, 0, Cn)
