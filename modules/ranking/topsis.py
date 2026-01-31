import pandas as pd
import numpy as np
from modules.base import RankingStrategy

class TOPSISRanking(RankingStrategy):
    def rank_alternatives(self, data: pd.DataFrame, weights: dict, criteria_type: dict, **kwargs) -> tuple[pd.DataFrame, dict]:
        # **kwargs akan menerima 'method_settings' nanti
        settings = kwargs.get('settings', {})
        metric = settings.get('topsis_metric', 'euclidean') # Default Euclidean

        df = data.copy()
        criteria = list(weights.keys())
        steps = {}

        # 1. Normalisasi (Vector / Akar Kuadrat Sum)
        norm_df = pd.DataFrame(index=df.index)
        denominator = np.sqrt((df[criteria]**2).sum())
        
        for col in criteria:
            norm_df[col] = df[col] / denominator[col] if denominator[col] != 0 else 0
            
        steps['1. Matriks Normalisasi (R)'] = norm_df.copy()

        # 2. Matriks Terbobot
        weighted_df = norm_df.copy()
        for col in criteria:
            weighted_df[col] = weighted_df[col] * weights[col]
            
        steps['2. Matriks Terbobot (Y)'] = weighted_df.copy()

        # 3. Solusi Ideal (Positif & Negatif)
        ideal_pos = {}
        ideal_neg = {}
        
        for col in criteria:
            if criteria_type[col] == 'benefit':
                ideal_pos[col] = weighted_df[col].max()
                ideal_neg[col] = weighted_df[col].min()
            else:
                ideal_pos[col] = weighted_df[col].min()
                ideal_neg[col] = weighted_df[col].max()
                
        df_ideal = pd.DataFrame([ideal_pos, ideal_neg], index=['Solusi Ideal Positif (A+)', 'Solusi Ideal Negatif (A-)'])
        steps['3. Solusi Ideal (A+ dan A-)'] = df_ideal

        # 4. Jarak ke Solusi Ideal (DINAMIS SESUAI SETTING)
        # Hitung jarak tiap baris terhadap Vector Ideal
        d_pos_list = []
        d_neg_list = []
        
        # Konversi Ideal ke Series agar mudah dihitung vector
        s_ideal_pos = pd.Series(ideal_pos)
        s_ideal_neg = pd.Series(ideal_neg)

        for idx, row in weighted_df.iterrows():
            diff_pos = row - s_ideal_pos
            diff_neg = row - s_ideal_neg
            
            if metric == 'manhattan':
                # Sum of Absolute Diff
                d_pos = diff_pos.abs().sum()
                d_neg = diff_neg.abs().sum()
            elif metric == 'chebyshev':
                # Max of Absolute Diff
                d_pos = diff_pos.abs().max()
                d_neg = diff_neg.abs().max()
            else: 
                # Euclidean (Sqrt of Sum Squares)
                d_pos = np.sqrt((diff_pos**2).sum())
                d_neg = np.sqrt((diff_neg**2).sum())
            
            d_pos_list.append(d_pos)
            d_neg_list.append(d_neg)

        df['D+'] = d_pos_list
        df['D-'] = d_neg_list
        
        # Simpan step jarak (Permintaan Anda sebelumnya)
        steps[f'4. Jarak Solusi Ideal ({metric.capitalize()})'] = df[['D+', 'D-']].copy()

        # 5. Nilai Preferensi (V)
        # V = D- / (D- + D+)
        # Handle division by zero
        df['TOPSIS_Score'] = df.apply(lambda r: r['D-'] / (r['D-'] + r['D+']) if (r['D-'] + r['D+']) != 0 else 0, axis=1)
        
        df['Rank'] = df['TOPSIS_Score'].rank(ascending=False).astype(int)
        
        return df.sort_values('Rank'), steps