from abc import ABC, abstractmethod
import pandas as pd

class WeightingStrategy(ABC):
    """
    Interface untuk metode pembobotan (AHP, ROC, Direct, dll).
    Output wajib: Dictionary { 'kriteria_A': 0.5, 'kriteria_B': 0.5 }
    """
    @abstractmethod
    def calculate_weight(self, data) -> dict:
        pass

class RankingStrategy(ABC):
    """
    Interface untuk metode perankingan (TOPSIS, SAW, MOORA, dll).
    Input: DataFrame Data Mentah (Belum Normalisasi) & Dictionary Bobot.
    Output: DataFrame dengan kolom tambahan 'Score' dan 'Rank'.
    """
    @abstractmethod
    def rank_alternatives(self, data: pd.DataFrame, weights: dict, criteria_type: dict) -> tuple[pd.DataFrame, dict]:
        pass