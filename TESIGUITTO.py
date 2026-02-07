# --- MOTORE DI CALCOLO SPERIMENTALE CON DEVIAZIONE ---
for _ in range(120):
    Cn = C.copy()
    Cn[src_x, src_y] += 1.2  # Sorgente

    for i in range(1, N-1):
        for j in range(1, N-1):
            if edifici_mask[i, j] == 1:
                continue
            
            # --- DIFFUSIONE INTELLIGENTE (Non "mangia" il gas) ---
            # Controlliamo quali vicini sono liberi
            vicini_liberi = []
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                if edifici_mask[i+dx, j+dy] == 0:
                    vicini_liberi.append(C[i+dx, j+dy])
            
            # Se ci sono palazzi intorno, la diffusione si concentra sui varchi liberi
            if len(vicini_liberi) > 0:
                diff = k_diff * dt * (sum(vicini_liberi) - len(vicini_liberi) * C[i,j])
            else:
                diff = 0

            # --- ADVEZIONE (VENTO) CON DEVIAZIONE ---
            # Se il vento (asse X) trova un palazzo davanti, 
            # forziamo una piccola componente laterale (asse Y)
            u_effettivo = u_base
            v_laterale = 0
            
            if edifici_mask[i+1, j] == 1: # Palazzo davanti
                u_effettivo = u_base * 0.1 # Il vento rallenta davanti al muro
                # Spingiamo il gas lateralmente per "aggirare"
                v_laterale = u_base * 0.5 * (C[i, j-1] - C[i, j+1]) 

            adv_x = -u_effettivo * dt * (C[i,j] - C[i-1,j])
            adv_y = v_laterale * dt
            
            Cn[i,j] += diff + adv_x + adv_y

    # Applichiamo la maschera finale
    C = np.where(edifici_mask == 1, 0, Cn)
