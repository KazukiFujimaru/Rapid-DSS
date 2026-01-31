import pandas as pd
import numpy as np

class AHPWeighting:
    def calculate_weight(self, pairwise_matrix: dict, cr_threshold=0.1):
        criteria = list(pairwise_matrix.keys())
        n = len(criteria)
        
        # 1. Buat Matrix NumPy
        mat = np.zeros((n, n))
        for i, r in enumerate(criteria):
            for j, c in enumerate(criteria):
                mat[i, j] = pairwise_matrix[r][c]
                
        # 2. Hitung Eigenvector (Bobot Prioritas)
        col_sum = mat.sum(axis=0)
        norm_mat = mat / col_sum
        weights = norm_mat.mean(axis=1)
        
        weight_dict = {c: weights[i] for i, c in enumerate(criteria)}
        
        # 3. Hitung Consistency Ratio (CR)
        # Lambda Max
        weighted_sum_vec = mat.dot(weights)
        lambda_max = (weighted_sum_vec / weights).mean()
        
        # Consistency Index (CI)
        ci = (lambda_max - n) / (n - 1) if n > 1 else 0
        
        # Random Index (RI) - Tabel Saaty
        ri_dict = {1:0, 2:0, 3:0.58, 4:0.9, 5:1.12, 6:1.24, 7:1.32, 8:1.41, 9:1.45, 10:1.49}
        ri = ri_dict.get(n, 1.49)
        
        # Consistency Ratio (CR)
        cr = ci / ri if ri != 0 else 0
        
        # 4. LOGIKA VALIDASI BARU
        # Jika CR melebihi batas yang disetting user
        if cr > cr_threshold:
            raise ValueError(f"Konsistensi Ratio (CR) = {cr:.4f}. Melebihi batas toleransi ({cr_threshold}). Mohon input ulang perbandingan agar lebih konsisten.")

        # Simpan Steps
        df_mat = pd.DataFrame(mat, index=criteria, columns=criteria)
        df_norm = pd.DataFrame(norm_mat, index=criteria, columns=criteria)
        
        steps = {
            '1. [AHP] Matriks Perbandingan Berpasangan': df_mat,
            '2. [AHP] Matriks Normalisasi': df_norm,
            '3. [AHP] Hasil CR (Consistency Ratio)': pd.DataFrame({
                'Lambda Max': [lambda_max], 'CI': [ci], 'RI': [ri], 'CR': [cr], 'Status': ['Valid' if cr <= cr_threshold else 'Tidak Konsisten']
            })
        }
        
        return weight_dict, steps