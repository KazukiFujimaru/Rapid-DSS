import pandas as pd
from modules.base import RankingStrategy

class SAWRanking(RankingStrategy):
    # TAMBAHKAN **kwargs DISINI
    def rank_alternatives(self, data: pd.DataFrame, weights: dict, criteria_type: dict, **kwargs) -> tuple[pd.DataFrame, dict]:
        df = data.copy()
        criteria_cols = list(weights.keys())
        steps = {}

        # 1. Normalisasi Matriks (Min-Max)
        norm_df = pd.DataFrame(index=df.index)
        
        for col in criteria_cols:
            if criteria_type[col] == 'benefit':
                max_val = df[col].max()
                norm_df[col] = df[col] / max_val if max_val != 0 else 0
            else:
                min_val = df[col].min()
                # Handle division by zero
                norm_df[col] = df[col].apply(lambda x: min_val / x if x != 0 else 0)
        
        steps['1. Normalisasi Matriks (R)'] = norm_df.copy()

        # 2. Perankingan (SAW Score)
        # Score = Sum(Norm * Weight)
        final_score = pd.Series(0.0, index=df.index)
        
        for col in criteria_cols:
            final_score += norm_df[col] * weights[col]

        df['SAW_Score'] = final_score
        df['Rank'] = df['SAW_Score'].rank(ascending=False).astype(int)

        return df.sort_values('Rank'), steps