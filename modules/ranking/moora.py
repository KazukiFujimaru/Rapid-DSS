import pandas as pd
import numpy as np
from modules.base import RankingStrategy

class MOORARanking(RankingStrategy):
    # TAMBAHKAN **kwargs DISINI
    def rank_alternatives(self, data: pd.DataFrame, weights: dict, criteria_type: dict, **kwargs) -> tuple[pd.DataFrame, dict]:
        df = data.copy()
        criteria_cols = list(weights.keys())
        steps = {}

        # 1. Normalisasi (X / Akar(Sum(X^2)))
        norm_df = pd.DataFrame(index=df.index)
        for col in criteria_cols:
            denom = np.sqrt((df[col]**2).sum())
            norm_df[col] = df[col] / denom if denom != 0 else 0
            
        steps['1. Matriks Normalisasi (Ratio)'] = norm_df.copy()

        # 2. Matriks Terbobot
        weighted_df = norm_df.copy()
        for col in criteria_cols:
            weighted_df[col] = weighted_df[col] * weights[col]
            
        steps['2. Matriks Terbobot'] = weighted_df.copy()

        # 3. Hitung Optimasi (Benefit - Cost)
        benefit_sum = pd.Series(0.0, index=df.index)
        cost_sum = pd.Series(0.0, index=df.index)

        for col in criteria_cols:
            if criteria_type[col] == 'benefit':
                benefit_sum += weighted_df[col]
            else:
                cost_sum += weighted_df[col]
        
        y_score = benefit_sum - cost_sum
        
        df_calc = pd.DataFrame({
            'Total Benefit (Max)': benefit_sum,
            'Total Cost (Min)': cost_sum,
            'Nilai Yi (Max - Min)': y_score
        })
        steps['3. Perhitungan Nilai Optimasi (Yi)'] = df_calc

        df['MOORA_Score'] = y_score
        df['Rank'] = df['MOORA_Score'].rank(ascending=False).astype(int)

        return df.sort_values('Rank'), steps