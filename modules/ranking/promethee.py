import pandas as pd
import numpy as np
from modules.base import RankingStrategy

class PrometheeRanking(RankingStrategy):
    def rank_alternatives(self, data: pd.DataFrame, weights: dict, criteria_type: dict, **kwargs) -> tuple[pd.DataFrame, dict]:
        settings = kwargs.get('settings', {})
        pref_type = settings.get('promethee_pref', 'usual')
        p_threshold = float(settings.get('promethee_p', 0))
        
        df = data.copy()
        alternatives = df.index.tolist()
        criteria = list(weights.keys())
        steps = {}
        
        # Matriks Preferensi (Aggregated)
        # Struktur: Baris=Alt A, Kolom=Alt B, Nilai=Seberapa besar A mengalahkan B (0-1)
        pref_matrix = pd.DataFrame(0.0, index=alternatives, columns=alternatives)
        
        # Detail perhitungan per kriteria (disimpan untuk debug/advanced view)
        # Kita hitung pairwise comparison
        
        for crit in criteria:
            w = weights[crit]
            is_benefit = criteria_type[crit] == 'benefit'
            
            # Loop Pairwise
            for a in alternatives:
                val_a = df.loc[a, crit]
                for b in alternatives:
                    if a == b: continue
                    
                    val_b = df.loc[b, crit]
                    
                    # Hitung Selisih (d)
                    if is_benefit:
                        d = val_a - val_b
                    else:
                        d = val_b - val_a # Cost: Kalau A lebih kecil dari B, A menang (d positif)
                    
                    # Hitung P(d) berdasarkan Tipe Fungsi
                    pref_val = 0.0
                    
                    if d <= 0:
                        pref_val = 0.0
                    else:
                        if pref_type == 'usual':
                            # Tipe 1: Strict (Menang sedikit = Menang total)
                            pref_val = 1.0
                        elif pref_type == 'linear':
                            # Tipe 5: Linear (Menang bertahap sampai threshold p)
                            if d >= p_threshold:
                                pref_val = 1.0
                            else:
                                pref_val = d / p_threshold if p_threshold != 0 else 1.0
                    
                    # Tambahkan ke matriks agregat (dikali bobot)
                    pref_matrix.loc[a, b] += pref_val * w

        steps['1. Matriks Preferensi Agregat (Pi)'] = pref_matrix.copy()

        # Hitung Leaving & Entering Flow
        # Leaving (Phi+): Rata-rata baris (Kekuatan mengalahkan orang lain)
        # Entering (Phi-): Rata-rata kolom (Kelemahan dikalahkan orang lain)
        
        n = len(alternatives)
        leaving_flow = pref_matrix.sum(axis=1) / (n - 1)
        entering_flow = pref_matrix.sum(axis=0) / (n - 1)
        
        net_flow = leaving_flow - entering_flow
        
        df_flows = pd.DataFrame({
            'Leaving Flow (Phi+)': leaving_flow,
            'Entering Flow (Phi-)': entering_flow,
            'Net Flow (Phi)': net_flow
        })
        
        steps['2. Leaving, Entering, & Net Flow'] = df_flows.copy()
        
        # PROMETHEE Score = Net Flow
        # Normalisasi Net Flow ke range 0-1 (Opsional, tapi Net Flow asli -1 s/d 1)
        # Kita pakai Net Flow asli saja untuk ranking
        
        df['PROMETHEE_Score'] = net_flow
        df['Rank'] = df['PROMETHEE_Score'].rank(ascending=False).astype(int)
        
        return df.sort_values('Rank'), steps