class DataStore:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataStore, cls).__new__(cls)
            
            # --- Inisialisasi Variable Penyimpanan ---
            cls._instance.df_original = None
            cls._instance.criteria_type = {}    # { 'Harga': 'cost', ... }
            cls._instance.selected_methods = {} # { 'ranking': 'topsis', ... }
            cls._instance.weights = {}          # { 'Harga': 0.2, ... }
            cls._instance.results = None        # DataFrame Hasil Akhir
            
            # Penyimpanan Langkah Perhitungan (Step-by-Step)
            cls._instance.weighting_steps = {} 
            
            # BARU: Penyimpanan Parameter Advanced (Promethee/TOPSIS Settings)
            cls._instance.method_settings = {} 
            
        return cls._instance

    def clear_data(self):
        """Reset semua data saat upload baru"""
        self.df_original = None
        self.criteria_type = {}
        self.selected_methods = {}
        self.weights = {}
        self.results = None
        self.weighting_steps = {}
        self.method_settings = {} # Reset juga settingan advanced