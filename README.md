# 🚀 Rapid DSS

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Flask](https://img.shields.io/badge/Framework-Flask-green)
![Status](https://img.shields.io/badge/Status-Active-success)

**Rapid DSS** adalah aplikasi Sistem Pendukung Keputusan (Decision Support System) berbasis web yang dirancang untuk membuat Sistem Pendukung Keputusan dengan cepat. Terinspirasi dari Rapid Miner yang dikembangkan untuk Machine Learning

## ✨ Fitur Utama

* **Multi-Method Support**: Untuk saat ini mendukung metode **SAW**, **WP**, **AHP**, **TOPSIS**, **PROMETHEE**, dan **MOORA**.
* **Dynamic Configuration**: Input kriteria dan alternatif yang fleksibel (bisa tambah/kurang kolom & baris).
* **Sensitivity Analysis**: Uji ketahanan keputusan dengan slider bobot interaktif (Real-time).
* **Visual Comparison**: Grafik Radar dan Bar Chart untuk membandingkan kandidat head-to-head.
* **Robustness Check**: Validasi hasil dengan membandingkan peringkat antar metode.

## 🛠️ Instalasi & Menjalankan Lokal

Jika Anda ingin menjalankan aplikasi ini di komputer lokal Anda:

1.  **Clone repositori**
    ```bash
    git clone [https://github.com/username-anda/rapid-dss.git](https://github.com/username-anda/rapid-dss.git)
    cd rapid-dss
    ```

2.  **Buat Virtual Environment (Opsional tapi disarankan)**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Jalankan Aplikasi**
    ```bash
    python app.py
    ```
    Buka browser di `http://127.0.0.1:5000`

## 📝 Lisensi

Project ini dibuat untuk keperluan tugas dan pengembangan riset operasional.