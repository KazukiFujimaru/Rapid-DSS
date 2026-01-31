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
    
    # --- 1. HOME (Hanya Upload & Fuzzy Check) ---
    @app.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "POST":
            df_temp = None
            
            # A. HANDLE CSV UPLOAD
            if 'file' in request.files and request.files['file'].filename != '':
                try: df_temp = pd.read_csv(request.files['file'])
                except Exception as e: return f"Error CSV: {e}"
            
            
            if df_temp is not None:
                ds.clear_data()
                ds.df_original = df_temp
                ds.df_original.columns = ds.df_original.columns.str.strip()
                return redirect(url_for('configure'))
                    
        return render_template("index.html")

    # --- 2. CONFIG (LOGIKA SETTINGS PINDAH KESINI) ---
    @app.route("/configure", methods=["GET", "POST"])
    def configure():
        if ds.df_original is None: return redirect(url_for('index'))
        
        first_col_name = ds.df_original.columns[0]
        
        if request.method == "POST":
            # 1. Simpan Kriteria
            selected = request.form.getlist('criteria')
            valid_criteria = [c for c in selected if c != first_col_name]
            
            if not valid_criteria:
                return "Error: Pilih minimal 1 kriteria (selain kolom Nama)."

            ds.criteria_type = {c: request.form.get(f'type_{c}') for c in valid_criteria}
            
            # 2. Simpan Pilihan Metode Utama
            ds.selected_methods = {
                'weighting': request.form.get('weighting_method'), 
                'ranking': request.form.get('ranking_method')
            }

            # 3. DEBUG & SIMPAN ADVANCED SETTINGS (DISINI TEMPATNYA)
            print("DEBUG SETTINGS DITERIMA:", {
                'topsis_metric': request.form.get('topsis_metric'),
                'promethee_pref': request.form.get('promethee_pref'),
                'promethee_p': request.form.get('promethee_p')
            })

            ds.method_settings = {
                'topsis_metric': request.form.get('topsis_metric', 'euclidean'),
                'promethee_pref': request.form.get('promethee_pref', 'usual'),
                'promethee_type': request.form.get('promethee_type', 'ii'),
                'promethee_p': float(request.form.get('promethee_p') or 0),
                'ahp_cr': float(request.form.get('ahp_cr') or 0.1)
            }
            
            # 4. Redirect ke Weighting
            w_method = ds.selected_methods['weighting']
            if w_method == 'ahp': return redirect(url_for('ahp_input'))
            elif w_method == 'likert': return redirect(url_for('likert_input'))
            else: return redirect(url_for('direct_weight_input'))
            
        return render_template("configure.html", columns=ds.df_original.columns.tolist())

    # --- 3. INPUT ROUTES ---
    @app.route("/direct_weight", methods=["GET", "POST"])
    def direct_weight_input():
        if request.method == "POST":
            raw = {k: float(request.form.get(k)) for k in ds.criteria_type.keys()}
            tot = sum(raw.values())
            ds.weights = {k: v/tot for k, v in raw.items()} if tot > 0 else raw
            
            df_step = pd.DataFrame(list(raw.items()), columns=['Kriteria', 'Input Mentah']).set_index('Kriteria')
            df_step['Bobot Ternormalisasi'] = pd.Series(ds.weights)
            ds.weighting_steps = {'1. [Manual] Input & Normalisasi': df_step}
            return redirect(url_for('result'))
        return render_template("weight_direct.html", criteria=list(ds.criteria_type.keys()))

    @app.route("/likert", methods=["GET", "POST"])
    def likert_input():
        if request.method == "POST":
            scores = {k: float(request.form.get(k)) for k in ds.criteria_type.keys()}
            ds.weights, ds.weighting_steps = LikertWeighting().calculate_weight(scores)
            return redirect(url_for('result'))
        return render_template("weight_likert.html", criteria=list(ds.criteria_type.keys()))

    @app.route("/ahp", methods=["GET", "POST"])
    def ahp_input():
        criteria = list(ds.criteria_type.keys())
        cr_limit = ds.method_settings.get('ahp_cr', 0.1)
        if request.method == "POST":
            matrix = {c: {c: 1.0 for c in criteria} for c in criteria}
            n = len(criteria)
            for i in range(n):
                for j in range(i+1, n):
                    c1, c2 = criteria[i], criteria[j]
                    val = int(request.form.get(f"{c1}_vs_{c2}"))
                    v_final = abs(val) if val < 0 else (1/val if val != 0 else 1.0)
                    if val == 0: v_final = 1.0
                    matrix[c1][c2] = v_final
                    matrix[c2][c1] = 1.0 / v_final
            ds.weights, ds.weighting_steps = AHPWeighting().calculate_weight(matrix)
            try:
                ds.weights, ds.weighting_steps = AHPWeighting().calculate_weight(matrix, cr_threshold=cr_limit)
                return redirect(url_for('result'))
            except ValueError as e:
                return render_template("ahp.html", criteria=criteria, error=str(e))
        return render_template("ahp.html", criteria=criteria)

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
        if not ds.weights: return redirect(url_for('configure'))

        method_name = ds.selected_methods.get('ranking', 'topsis')
        ranker, algo_title = get_ranker_instance(method_name)
        
        name_col = ds.df_original.columns[0]
        data_clean = ds.df_original.set_index(name_col)[list(ds.criteria_type.keys())]
        
        # FIX: KIRIM SETTINGS KE RANKER
        df_res, ranking_steps = ranker.rank_alternatives(
            data_clean, 
            ds.weights, 
            ds.criteria_type, 
            settings=ds.method_settings
        )
        ds.results = df_res

        all_steps = {}
        if ds.weighting_steps: all_steps.update(ds.weighting_steps)
        all_steps.update(ranking_steps)
        
        formatted_steps_html = {}
        for k, v in all_steps.items():
            temp_df = v.copy()
            if temp_df.index.name is None:
                if any(x in k for x in ["[AHP]", "[Likert]", "Bobot"]): temp_df.index.name = "Kriteria"
                else: temp_df.index.name = "Alternatif"
            formatted_steps_html[k] = temp_df.reset_index().to_html(classes='table table-sm table-striped table-hover mb-0', index=False, float_format="%.4f")

        df_top3 = df_res.sort_values('Rank').head(3)
        heatmap_full = list(ranking_steps.values())[0].copy()
        for col in heatmap_full.columns:
            mx, mn = heatmap_full[col].max(), heatmap_full[col].min()
            heatmap_full[col] = (heatmap_full[col] - mn)/(mx-mn) if mx!=mn else 1.0
        
        heatmap_top3 = heatmap_full.loc[df_top3.index]
        chart_data = _prepare_chart_data(heatmap_top3, df_res)

        df_res_display = df_res.copy()
        if df_res_display.index.name is None: df_res_display.index.name = "Alternatif"

        return render_template("result.html", 
                               result_html=df_res_display.reset_index().to_html(classes='table table-striped table-bordered mb-0 table-hover', index=False),
                               steps=formatted_steps_html,
                               heatmap_full=heatmap_full,
                               top3_html=df_top3.reset_index().to_html(classes='table table-sm table-borderless table-hover mb-0', index=False),
                               heatmap_top3=heatmap_top3,
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
            # FIX: Kirim settings juga ke sini jika perlu (misal PROMETHEE vs TOPSIS comparison)
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

    # --- 6. API: RECALCULATE ---
    @app.route("/api/recalculate", methods=["POST"])
    def api_recalculate():
        try:
            raw = request.json
            tot = sum(raw.values())
            new_w = {k: 1/len(raw) for k in raw} if tot==0 else {k: v/tot for k, v in raw.items()}
            
            method_name = ds.selected_methods.get('ranking', 'topsis')
            ranker, _ = get_ranker_instance(method_name)
            
            name_col = ds.df_original.columns[0]
            data = ds.df_original.set_index(name_col)[list(ds.criteria_type.keys())]
            
            # FIX: Kirim settings ke Ranker
            df_res, _ = ranker.rank_alternatives(data, new_w, ds.criteria_type, settings=ds.method_settings)

            df_display = df_res.copy()
            if df_display.index.name is None: df_display.index.name = "Alternatif"
            df_display = df_display.reset_index()

            def highlight_winner(s):
                return ['background-color: #d1e7dd; font-weight: bold;' if s['Rank'] == 1 else '' for _ in s]

            table_html = df_display.style.apply(highlight_winner, axis=1)\
                                   .format("{:,.4f}", subset=pd.IndexSlice[:, df_display.select_dtypes(include='float').columns])\
                                   .hide(axis="index")\
                                   .to_html(classes='table table-striped table-hover mb-0 align-middle w-100', table_id="predictionTable")

            score_col = f"{method_name.upper()}_Score"
            fixed = df_res.sort_index()
            
            chart = {
                'labels': fixed.index.tolist(),
                'datasets': [{
                    'label': f'Skor ({method_name.upper()})', 
                    'data': fixed[score_col].tolist(), 
                    'backgroundColor': 'rgba(54, 162, 235, 0.6)', 
                    'borderColor': 'blue', 
                    'borderWidth': 1, 
                    'fill': True
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