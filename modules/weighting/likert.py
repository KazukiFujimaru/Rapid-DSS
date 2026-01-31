import pandas as pd
from modules.base import WeightingStrategy

class LikertWeighting(WeightingStrategy):
    def calculate_weight(self, criteria_scores: dict) -> tuple[dict, dict]:
        steps = {}
        
        # 1. Tampilkan Input Mentah
        df_raw = pd.DataFrame(list(criteria_scores.items()), columns=['Kriteria', 'Nilai Input (1-5)'])
        df_raw.set_index('Kriteria', inplace=True)
        steps['1. [Likert] Input Penilaian User'] = df_raw
        
        # 2. Normalisasi
        total_score = sum(criteria_scores.values())
        if total_score == 0:
            weights = {k: 1/len(criteria_scores) for k in criteria_scores}
        else:
            weights = {k: v / total_score for k, v in criteria_scores.items()}
            
        # Tampilkan Proses Bagi Total
        df_calc = df_raw.copy()
        df_calc['Total Nilai'] = total_score
        df_calc['Bobot (Nilai / Total)'] = df_calc['Nilai Input (1-5)'] / total_score
        steps['2. [Likert] Perhitungan Normalisasi'] = df_calc[['Nilai Input (1-5)', 'Total Nilai', 'Bobot (Nilai / Total)']]
        
        return weights, steps