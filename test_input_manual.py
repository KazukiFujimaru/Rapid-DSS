import pandas as pd
from modules.weighting.ahp import AHPWeighting
from modules.ranking.topsis import TOPSISRanking

# 1. Test Data Dummy
data = pd.DataFrame({
    'Alternatif': ['Laptop A', 'Laptop B', 'Laptop C'],
    'Harga': [5000000, 8000000, 6000000],   # Cost
    'RAM': [8, 16, 8],                      # Benefit
    'Baterai': [4000, 5000, 4500]           # Benefit
}).set_index('Alternatif')

criteria_type = {'Harga': 'cost', 'RAM': 'benefit', 'Baterai': 'benefit'}

# 2. Test AHP (Misal Harga 2x lebih penting dari RAM)
ahp_input = {
    'Harga': {'Harga': 1, 'RAM': 2, 'Baterai': 3},
    'RAM': {'Harga': 0.5, 'RAM': 1, 'Baterai': 2},
    'Baterai': {'Harga': 0.33, 'RAM': 0.5, 'Baterai': 1}
}

print("=== RUNNING AHP ===")
ahp = AHPWeighting()
weights = ahp.calculate_weight(ahp_input)
print("Bobot AHP:", weights)

# 3. Test TOPSIS
print("\n=== RUNNING TOPSIS ===")
topsis = TOPSISRanking()
result = topsis.rank_alternatives(data, weights, criteria_type)
print(result[['Harga', 'RAM', 'Baterai', 'TOPSIS_Score', 'Rank']])