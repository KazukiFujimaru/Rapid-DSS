import pandas as pd
from modules.base import RankingStrategy

class WPRanking(RankingStrategy):
    # TAMBAHKAN **kwargs DISINI
    def rank_alternatives(self, data: pd.DataFrame, weights: dict, criteria_type: dict, **kwargs) -> tuple[pd.DataFrame, dict]:
        df = data.copy()
        criteria_cols = list(weights.keys())
        steps = {}

        # 1. Pangkatkan Nilai (S Vector)
        s_vector = pd.Series(1.0, index=df.index)
        df_power = pd.DataFrame(index=df.index)

        for col in criteria_cols:
            w = weights[col]
            # WP: Cost pangkatnya negatif
            if criteria_type[col] == 'cost':
                w = -w
            
            val_pow = df[col].pow(w)
            df_power[col] = val_pow
            s_vector = s_vector * val_pow

        steps['1. Perpangkatan Bobot (Vector S)'] = df_power.copy()
        
        df_s = pd.DataFrame(s_vector, columns=['Nilai S'])
        steps['2. Hasil Vector S'] = df_s.copy()

        # 2. Preferensi Relatif (V Vector)
        total_s = s_vector.sum()
        v_vector = s_vector / total_s if total_s != 0 else 0

        df['WP_Score'] = v_vector
        df['Rank'] = df['WP_Score'].rank(ascending=False).astype(int)

        return df.sort_values('Rank'), steps