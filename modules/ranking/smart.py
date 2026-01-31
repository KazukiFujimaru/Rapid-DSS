import pandas as pd
from modules.base import RankingStrategy

class SMARTRanking(RankingStrategy):
    # TAMBAHKAN **kwargs DISINI
    def rank_alternatives(self, data: pd.DataFrame, weights: dict, criteria_type: dict, **kwargs) -> tuple[pd.DataFrame, dict]:
        df = data.copy()
        criteria_cols = list(weights.keys())
        steps = {}

        # 1. Menghitung Nilai Utility (Ui)
        utility_df = pd.DataFrame(index=df.index)
        
        for col in criteria_cols:
            c_min = df[col].min()
            c_max = df[col].max()
            
            if c_max == c_min:
                utility_df[col] = 1.0 
            else:
                if criteria_type[col] == 'benefit':
                    utility_df[col] = (df[col] - c_min) / (c_max - c_min)
                else:
                    utility_df[col] = (c_max - df[col]) / (c_max - c_min)
                    
        steps['1. Nilai Utility (Normalisasi)'] = utility_df.copy()

        # 2. Nilai Akhir (Weighted Sum)
        final_score = pd.Series(0.0, index=df.index)
        for col in criteria_cols:
            final_score += utility_df[col] * weights[col]

        df['SMART_Score'] = final_score
        df['Rank'] = df['SMART_Score'].rank(ascending=False).astype(int)

        return df.sort_values('Rank'), steps