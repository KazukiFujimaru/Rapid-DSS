import pandas as pd
import io
import json
from flask import render_template, request, redirect, url_for, jsonify
from modules.datastore import DataStore

# Import Semua Algoritma Ranking
from modules.weighting.ahp import AHPWeighting
from modules.weighting.likert import LikertWeighting
from modules.ranking.topsis import TOPSISRanking
from modules.ranking.saw import SAWRanking
from modules.ranking.wp import WPRanking
from modules.ranking.moora import MOORARanking
from modules.ranking.smart import SMARTRanking
from modules.ranking.promethee import PrometheeRanking

ds = DataStore()

def configure_routes(app):
    
    # --- 1. HOME (Upload & Manual Input) ---
    @app.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "POST":
            df_temp = None
            
            # A. HANDLE CSV UPLOAD
            if 'file' in request.files and request.files['file'].filename != '':
                try: 
                    df_temp = pd.read_csv(request.files['file'])
                except Exception as e: 
                    return f"Error CSV: {e}"
            
            # B. HANDLE MANUAL INPUT
            elif 'manual_data' in request.form and request.form['manual_data'].strip():
                raw_text = request.form['manual_data']
                clean_text = raw_text.replace("#MODE:FUZZY#\n", "").replace("#MODE:CRISP#\n", "")
                try: 
                    df_temp = pd.read_csv(io.StringIO(clean_text), sep=None, engine='python')
                except Exception as e: 
                    return f"Error Manual Input: {e}"
            
            # C. SIMPAN DATA
            if df_temp is not None:
                ds.clear_data()
                ds.df_original = df_temp
                ds.df_original.columns = ds.df_original.columns.str.strip()
                return redirect(url_for('configure'))
                    
        return render_template("index.html")

    # --- 2. CONFIG ---
    @app.route("/configure", methods=["GET", "POST"])
    def configure():
        if ds.df_original is None: return redirect(url_for('index'))
        
        first_col_name = ds.df_original.columns[0]
        
        if request.method == "POST":
            selected = request.form.getlist('criteria')
            valid_criteria = [c for c in selected if c != first_col_name]
            
            if not valid_criteria:
                return "Error: Pilih minimal 1 kriteria."

            ds.criteria_type = {c: request.form.get(f'type_{c}') for c in valid_criteria}
            
            ds.selected_methods = {
                'weighting': request.form.get('weighting_method'), 
                'ranking': request.form.get('ranking_method')
            }

            ds.method_settings = {
                'topsis_metric': request.form.get('topsis_metric', 'euclidean'),
                'promethee_pref': request.form.get('promethee_pref', 'usual'),
                'promethee_type': request.form.get('promethee_type', 'ii'),
                'promethee_p': float(request.form.get('promethee_p') or 0),
                'ahp_cr': float(request.form.get('ahp_cr') or 0.1)
            }
            
            w_method = ds.selected_methods['weighting']
            if w_method == 'ahp': return redirect(url_for('ahp_input'))
            elif w_method == 'likert': return redirect(url_for('likert_input'))
            else: return redirect(url_for('direct_weight_input'))
            
        return render_template("configure.html", columns=ds.df_original.columns.tolist())

    # --- 3. INPUT ROUTES (FIXED PREFIXES) ---
    
    @app.route("/direct_weight", methods=["GET", "POST"])
    def direct_weight_input():
        if request.method == "POST":
            # FIX: Tambahkan prefix 'w_' sesuai HTML weight_direct.html
            try:
                raw = {k: float(request.form.get(f'w_{k}')) for k in ds.criteria_type.keys()}
                tot = sum(raw.values())
                # Hindari pembagian dengan nol
                ds.weights = {k: v/tot for k, v in raw.items()} if tot > 0 else raw
                
                df_step = pd.DataFrame(list(raw.items()), columns=['Kriteria', 'Input Mentah']).set_index('Kriteria')
                df_step['Bobot Ternormalisasi'] = pd.Series(ds.weights)
                ds.weighting_steps = {'1. [Manual] Input & Normalisasi': df_step}
                return redirect(url_for('result'))
            except ValueError:
                 return render_template("weight_direct.html", criteria=list(ds.criteria_type.keys()), error="Input harus berupa angka valid.")
                 
        return render_template("weight_direct.html", criteria=list(ds.criteria_type.keys()))

    @app.route("/likert", methods=["GET", "POST"])
    def likert_input():
        if request.method == "POST":
            # FIX: Tambahkan prefix 'l_' sesuai HTML weight_likert.html
            try:
                scores = {k: float(request.form.get(f'l_{k}')) for k in ds.criteria_type.keys()}
                ds.weights, ds.weighting_steps = LikertWeighting().calculate_weight(scores)
                return redirect(url_for('result'))
            except ValueError:
                return render_template("weight_likert.html", criteria=list(ds.criteria_type.keys()), error="Terjadi kesalahan membaca input.")
                
        return render_template("weight_likert.html", criteria=list(ds.criteria_type.keys()))

    @app.route("/ahp", methods=["GET", "POST"])
    def ahp_input():
        criteria = list(ds.criteria_type.keys())
        n = len(criteria)
        cr_limit = ds.method_settings.get('ahp_cr', 0.1)
        
        if request.method == "POST":
            try:
                # 1. Bangun Matriks dari Input Form
                matrix = {c: {c: 1.0 for c in criteria} for c in criteria}
                
                for i in range(n):
                    for j in range(i+1, n):
                        c1, c2 = criteria[i], criteria[j]
                        
                        val_str = request.form.get(f"c_{i}_vs_{j}")
                        if val_str is None: continue # Skip jika data hilang
                            
                        val = int(val_str)
                        
                        # Logika Saaty: Ubah -9 s.d 9 menjadi bobot 1/9 s.d 9
                        v_final = abs(val) if val < 0 else (1/val if val != 0 else 1.0)
                        if val == 0: v_final = 1.0
                        
                        matrix[c1][c2] = v_final
                        matrix[c2][c1] = 1.0 / v_final
                
                # 2. Hitung Bobot AHP (DENGAN TRY-EXCEPT)
                # Catatan: calculate_weight akan me-raise ValueError jika CR > cr_limit
                ds.weights, ds.weighting_steps = AHPWeighting().calculate_weight(matrix, cr_threshold=cr_limit)
                
                # Jika sukses (tidak error), lanjut ke result
                return redirect(url_for('result'))
            
            except ValueError as e:
                # 3. TANGKAP ERROR (Konsistensi Buruk)
                # Tampilkan kembali halaman AHP dengan pesan error merah
                return render_template("ahp.html", criteria=criteria, error=str(e), matrix_size=n)
                
            except Exception as e:
                # Tangkap error lain yang tidak terduga
                return render_template("ahp.html", criteria=criteria, error=f"Terjadi kesalahan sistem: {str(e)}", matrix_size=n)
                
        return render_template("ahp.html", criteria=criteria, matrix_size=n)

    # --- HELPER: SELECT RANKER ---
    def get_ranker_instance(method_name):
        if method_name == 'saw': return SAWRanking(), "SAW (Simple Additive Weighting)"
        elif method_name == 'wp': return WPRanking(), "WP (Weighted Product)"
        elif method_name == 'moora': return MOORARanking(), "MOORA (Ratio Analysis)"
        elif method_name == 'smart': return SMARTRanking(), "SMART (Utility Theory)"
        elif method_name == 'promethee': return PrometheeRanking(), "PROMETHEE (Outranking)"
        else: return TOPSISRanking(), "TOPSIS (Ideal Solution)"

    # --- 4. RESULT ---
    @app.route("/result")
    def result():
        # 1. Validasi
        if not ds.weights: return redirect(url_for('configure'))

        # 2. Hitung Ranking
        method_name = ds.selected_methods.get('ranking', 'topsis')
        ranker, algo_title = get_ranker_instance(method_name)
        
        name_col = ds.df_original.columns[0]
        data_clean = ds.df_original.set_index(name_col)[list(ds.criteria_type.keys())]
        
        df_res, ranking_steps = ranker.rank_alternatives(
            data_clean, 
            ds.weights, 
            ds.criteria_type, 
            settings=ds.method_settings
        )
        ds.results = df_res

        # 3. Format Tabel Rincian (Tetap HTML String)
        all_steps = {}
        if ds.weighting_steps: all_steps.update(ds.weighting_steps)
        all_steps.update(ranking_steps)
        
        formatted_steps_html = {}
        for k, v in all_steps.items():
            temp_df = v.copy()
            if temp_df.index.name is None:
                if any(x in k for x in ["[AHP]", "[Likert]", "Bobot"]): temp_df.index.name = "Kriteria"
                else: temp_df.index.name = "Alternatif"
            
            formatted_steps_html[k] = temp_df.reset_index().to_html(
                classes='table table-bordered table-striped table-hover mb-0 text-center small', 
                index=False, 
                float_format="%.4f"
            )

        # 4. Siapkan Data Heatmap (KIRIM DATAFRAME MENTAH!)
        # Normalisasi data 0-1
        heatmap_full = list(ranking_steps.values())[0].copy() 
        for col in heatmap_full.columns:
            mx, mn = heatmap_full[col].max(), heatmap_full[col].min()
            heatmap_full[col] = (heatmap_full[col] - mn)/(mx-mn) if mx!=mn else 1.0

        # Ambil Top 3
        df_top3 = df_res.sort_values('Rank').head(3)
        heatmap_top3 = heatmap_full.loc[df_top3.index]

        # Reset index agar 'Alternatif' bisa diakses sebagai kolom di Jinja2
        # Kita TIDAK convert ke .to_html() disini!
        heatmap_full_raw = heatmap_full.reset_index().rename(columns={heatmap_full.index.name: 'Alternatif'})
        heatmap_top3_raw = heatmap_top3.reset_index().rename(columns={heatmap_top3.index.name: 'Alternatif'})
        
        # Pastikan nama kolom index konsisten (jika reset_index membuat nama 'index')
        if 'index' in heatmap_full_raw.columns:
             heatmap_full_raw.rename(columns={'index': 'Alternatif'}, inplace=True)
             heatmap_top3_raw.rename(columns={'index': 'Alternatif'}, inplace=True)

        # 5. Chart & Leaderboard
        chart_data = _prepare_chart_data(heatmap_top3, df_res)

        df_res_display = df_res.copy()
        if df_res_display.index.name is None: df_res_display.index.name = "Alternatif"
        
        result_html = df_res_display.reset_index().to_html(
            classes='table table-bordered table-striped table-hover mb-0 leaderboard-table align-middle', 
            index=False,
            float_format="%.4f"
        )

        return render_template("result.html", 
                               result_html=result_html,
                               steps=formatted_steps_html,
                               heatmap_full=heatmap_full_raw, # Kirim DataFrame Asli
                               heatmap_top3=heatmap_top3_raw, # Kirim DataFrame Asli
                               weights=ds.weights,
                               chart_data=json.dumps(chart_data),
                               algo_title=algo_title)

    # --- 5. ANALYSIS PAGE ---
    @app.route("/analysis")
    def analysis():
        if not ds.weights: return redirect(url_for('configure'))
        name_col = ds.df_original.columns[0]
        data_clean = ds.df_original.set_index(name_col)[list(ds.criteria_type.keys())]

        methods_map = {
            'TOPSIS': TOPSISRanking(),
            'SAW': SAWRanking(),
            'WP': WPRanking(),
            'MOORA': MOORARanking(),
            'SMART': SMARTRanking()
        }
        
        methods_data = {}
        for m_name, m_class in methods_map.items():
            score_key = f"{m_name}_Score"
            res, _ = m_class.rank_alternatives(data_clean, ds.weights, ds.criteria_type, settings=ds.method_settings)
            methods_data[m_name] = res.rename(columns={score_key: 'Score'}).to_dict(orient='index')

        df_norm = data_clean.copy()
        for col in df_norm.columns:
            if ds.criteria_type[col] == 'benefit': df_norm[col] = df_norm[col]/df_norm[col].max()
            else: 
                mn = df_norm[col].min()
                df_norm[col] = df_norm[col].apply(lambda x: mn/x if x!=0 else 0)

        return render_template("analysis.html", 
                               weights=ds.weights, 
                               alternatives=data_clean.index.tolist(),
                               criteria_type=ds.criteria_type,
                               json_raw=data_clean.to_json(orient='index'),
                               json_norm=df_norm.to_json(orient='index'),
                               methods_data=methods_data,
                               current_method=ds.selected_methods.get('ranking','topsis').upper())

    # --- 6. API: RECALCULATE (FIXED TABLE STYLE) ---
    @app.route("/api/recalculate", methods=["POST"])
    def api_recalculate():
        try:
            raw = request.json
            tot = sum(raw.values())
            # Normalisasi bobot baru (agar total 1.0)
            new_w = {k: 1/len(raw) for k in raw} if tot==0 else {k: v/tot for k, v in raw.items()}
            
            # Hitung Ulang Ranking (Simple SAW Logic untuk Simulasi Cepat)
            name_col = ds.df_original.columns[0]
            df = ds.df_original.set_index(name_col)[list(ds.criteria_type.keys())].copy()
            
            scores = pd.Series(0.0, index=df.index)
            
            # Normalisasi Data & Kali Bobot
            for col, w in new_w.items():
                val = df[col]
                if ds.criteria_type.get(col) == 'cost':
                    mn = val.min()
                    norm = mn / val if mn > 0 else 0 
                else:
                    mx = val.max()
                    norm = val / mx if mx > 0 else 0
                scores += norm * w
            
            # Buat DataFrame Hasil
            res_df = pd.DataFrame({
                'Score': scores, 
                'Rank': scores.rank(ascending=False).astype(int)
            }).sort_values('Rank')
            
            # Gabungkan dengan Data Asli agar tabel informatif
            final_df = ds.df_original.set_index(name_col).join(res_df[['Score', 'Rank']], how='inner').sort_values('Rank')
            
            # FORMAT TABEL AGAR PROFESIONAL (Bootstrap Classes)
            table_html = final_df.reset_index().to_html(
                classes='table table-bordered table-striped table-hover mb-0 text-center small align-middle',
                index=False,
                float_format="%.4f",
                table_id="simTable"
            )

            # Data untuk Chart
            chart = {
                'labels': res_df.index.tolist(),
                'datasets': [{
                    'label': 'Skor Simulasi', 
                    'data': res_df['Score'].tolist(), 
                    'backgroundColor': 'rgba(54, 162, 235, 0.6)', 
                    'borderColor': '#0d6efd', 
                    'borderWidth': 1
                }]
            }
            
            return jsonify({'status': 'success', 'html_table': table_html, 'chart_data': chart})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    def _prepare_chart_data(norm_df, res_df):
        top3 = res_df.sort_values('Rank').head(3).index.tolist()
        datasets = []
        colors = ['rgba(255, 99, 132, 0.5)', 'rgba(54, 162, 235, 0.5)', 'rgba(255, 206, 86, 0.5)']
        borders = ['rgba(255, 99, 132, 1)', 'rgba(54, 162, 235, 1)', 'rgba(255, 206, 86, 1)']
        for i, alt in enumerate(top3):
            datasets.append({'label': alt, 'data': norm_df.loc[alt].tolist(), 'backgroundColor': colors[i%3], 'borderColor': borders[i%3], 'borderWidth': 2})
        return {'labels': norm_df.columns.tolist(), 'datasets': datasets}