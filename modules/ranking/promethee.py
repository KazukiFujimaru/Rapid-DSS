import pandas as pd
import numpy as np
import math
from modules.base import RankingStrategy

class PrometheeRanking(RankingStrategy):
    def rank_alternatives(self, data: pd.DataFrame, weights: dict, criteria_type: dict, **kwargs) -> tuple[pd.DataFrame, dict]:
        settings = kwargs.get('settings', {})
        
        # Ambil Parameter
        pref_type = settings.get('promethee_pref', 'usual')
        p_val = float(settings.get('promethee_p') or 0)
        q_val = float(settings.get('promethee_q') or 0) # Parameter baru
        s_val = float(settings.get('promethee_s') or 0) # Parameter baru
        
        df = data.copy()
        alternatives = df.index.tolist()
        criteria = list(weights.keys())
        steps = {}
        
        # Inisialisasi Matriks Preferensi
        pref_matrix = pd.DataFrame(0.0, index=alternatives, columns=alternatives)
        
        for crit in criteria:
            w = weights[crit]
            is_benefit = criteria_type[crit] == 'benefit'
            
            col_data = df[crit].to_numpy() # Optimisasi pakai NumPy array biar cepat
            
            # Loop manual masih oke untuk data kecil (Rapid-DSS)
            # Tapi kita gunakan logika fungsi preferensi yang lengkap
            for i, a in enumerate(alternatives):
                val_a = col_data[i]
                for j, b in enumerate(alternatives):
                    if i == j: continue
                    val_b = col_data[j]
                    
                    # 1. Hitung Selisih (d)
                    d = (val_a - val_b) if is_benefit else (val_b - val_a)
                    
                    # 2. Hitung Nilai Preferensi P(d)
                    pref_val = 0.0
                    
                    if d <= 0:
                        pref_val = 0.0
                    else:
                        if pref_type == 'usual': # Tipe 1
                            pref_val = 1.0
                        
                        elif pref_type == 'ushape': # Tipe 2 (Quasi)
                            pref_val = 1.0 if d > q_val else 0.0
                            
                        elif pref_type == 'vshape': # Tipe 3 (Linear Criterion)
                            pref_val = d / p_val if (p_val > 0 and d <= p_val) else 1.0
                            
                        elif pref_type == 'level': # Tipe 4 (Level)
                            if d <= q_val: pref_val = 0.0
                            elif d <= p_val: pref_val = 0.5
                            else: pref_val = 1.0
                            
                        elif pref_type == 'linear': # Tipe 5 (Linear w/ Indifference)
                            if d <= q_val: pref_val = 0.0
                            elif d <= p_val: pref_val = (d - q_val) / (p_val - q_val) if (p_val - q_val) != 0 else 1.0
                            else: pref_val = 1.0
                            
                        elif pref_type == 'gaussian': # Tipe 6 (Gaussian)
                            if s_val != 0:
                                pref_val = 1 - math.exp(-(d**2) / (2 * (s_val**2)))
                            else:
                                pref_val = 1.0 # Fallback jika s=0
                    
                    # Akumulasi ke matriks global
                    pref_matrix.iloc[i, j] += pref_val * w

        steps['1. Matriks Preferensi Agregat (Pi)'] = pref_matrix.copy()

        # Hitung Flows (PROMETHEE II)
        n = len(alternatives)
        if n > 1:
            leaving_flow = pref_matrix.sum(axis=1) / (n - 1)
            entering_flow = pref_matrix.sum(axis=0) / (n - 1)
        else:
            leaving_flow = pd.Series(0, index=alternatives)
            entering_flow = pd.Series(0, index=alternatives)
            
        net_flow = leaving_flow - entering_flow
        
        df_flows = pd.DataFrame({
            'Leaving (Phi+)': leaving_flow,
            'Entering (Phi-)': entering_flow,
            'Net Flow (Phi)': net_flow
        })
        
        steps['2. Flows Calculation'] = df_flows.copy()
        
        # Final Ranking
        df['PROMETHEE_Score'] = net_flow
        df['Rank'] = df['PROMETHEE_Score'].rank(ascending=False).astype(int)
        
        return df.sort_values('Rank'), steps