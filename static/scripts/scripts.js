/**
 * MAIN SCRIPT - RAPID DSS (Final Optimized Version)
 * Status: Verified Complete & Clean
 */

document.addEventListener("DOMContentLoaded", function() {
    // 1. Init Global (Tooltip, dll)
    initGlobal();

    // 2. Routing Logic (Page Guard)
    if (document.getElementById('rankingMethod')) initConfigurePage();
    if (document.getElementById('dynamicTable')) initIndexPage();
    if (document.querySelector('input[name*="_vs_"]')) initAhpPage();
    if (document.getElementById('radarChart')) initResultPage();
    if (document.getElementById('analysisTab')) initAnalysisPage();
});

/* ================= 1. GLOBAL & HELPER ================= */
function initGlobal() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (el) { return new bootstrap.Tooltip(el); });
}

// FUNGSI GLOBAL: Agar tombol HTML bisa akses kapan saja
window.processManualData = function() {
    console.log("Processing manual data...");
    
    const hiddenInput = document.getElementById('manualDataInput');
    const form = document.getElementById('formManual');
    if (!hiddenInput || !form) { alert("Error: Form tidak ditemukan. Refresh halaman."); return; }

    let csvContent = "";
    
    // 1. Header
    const headers = ["Alternatif"]; 
    const headerInputs = document.querySelectorAll('#headerRow th.group-header input');
    if (headerInputs.length === 0) { alert("Minimal 1 Kriteria."); return; }
    headerInputs.forEach(input => headers.push(input.value.trim() || "Kriteria"));
    csvContent += headers.join(",") + "\n";

    // 2. Rows
    const rows = document.querySelectorAll('#tableBody tr');
    if (rows.length === 0) { alert("Minimal 1 Alternatif."); return; }

    rows.forEach(row => {
        let rowData = [];
        const inputs = row.querySelectorAll('input');
        inputs.forEach((input, index) => {
            let val = input.value.trim();
            if(val === "" && index > 0) val = "0"; 
            if(val === "" && index === 0) val = "Alternatif " + (index+1);
            rowData.push(val);
        });
        csvContent += rowData.join(",") + "\n";
    });

    // 3. Submit
    hiddenInput.value = csvContent;
    form.submit();
};

/* ================= 2. HALAMAN INDEX ================= */
function initIndexPage() {
    window.addColumn = function() {
        const headerRow = document.getElementById('headerRow');
        const newTh = document.createElement('th');
        newTh.className = "position-relative group-header bg-light"; 
        let count = headerRow.children.length - 1;
        newTh.innerHTML = `<input type="text" class="form-control form-control-sm fw-bold text-center border-0 bg-transparent mb-1" value="C${count}">
                           <button type="button" class="btn btn-link text-danger p-0 position-absolute top-0 end-0 me-1" style="font-size:0.7rem;text-decoration:none;" onclick="removeColumn(this)">✕</button>`;
        headerRow.appendChild(newTh);

        document.querySelectorAll('#tableBody tr').forEach(row => {
            const newTd = document.createElement('td');
            newTd.innerHTML = `<input type="number" step="any" class="form-control form-control-sm text-center" placeholder="0">`;
            row.insertBefore(newTd, row.lastElementChild);
        });
    };

    window.removeColumn = function(btn) {
        const th = btn.closest('th');
        const index = Array.from(th.parentNode.children).indexOf(th);
        if (document.querySelectorAll('#headerRow th.group-header').length <= 1) { alert("Minimal 1 kriteria."); return; }
        th.remove();
        document.querySelectorAll('#tableBody tr').forEach(row => { if (row.children[index]) row.children[index].remove(); });
    };

    window.addRow = function() {
        const tbody = document.getElementById('tableBody');
        const colCount = document.querySelectorAll('#headerRow th.group-header').length;
        const rowCount = tbody.children.length + 1;
        const tr = document.createElement('tr');
        let html = `<td class="text-muted text-center">${rowCount}</td><td><input type="text" class="form-control form-control-sm" value="A${rowCount}"></td>`;
        for (let i = 0; i < colCount; i++) html += `<td><input type="number" step="any" class="form-control form-control-sm text-center" placeholder="0"></td>`;
        html += `<td class="text-center"><button class="btn btn-link text-danger p-0" onclick="removeRow(this)">✕</button></td>`;
        tr.innerHTML = html;
        tbody.appendChild(tr);
    };

    window.removeRow = function(btn) {
        const row = btn.closest('tr');
        if (document.getElementById('tableBody').children.length > 1) {
            row.remove();
            document.querySelectorAll('#tableBody tr').forEach((r, i) => { r.firstElementChild.innerText = i + 1; });
        } else { alert("Minimal 1 alternatif."); }
    };
}

/* ================= 3. HALAMAN CONFIGURE ================= */
function initConfigurePage() {
    const rankSelect = document.getElementById('rankingMethod');
    const weightSelect = document.querySelector('select[name="weighting_method"]');
    const promPrefSelect = document.getElementById('prom_pref_select');

    if(rankSelect) rankSelect.addEventListener('change', updateAdvancedOptions);
    if(weightSelect) weightSelect.addEventListener('change', updateAdvancedOptions);
    if(promPrefSelect) promPrefSelect.addEventListener('change', updatePrometheeInputs);
    updateAdvancedOptions();
}

function updateAdvancedOptions() {
    const rankMethod = document.getElementById('rankingMethod').value;
    const weightMethod = document.querySelector('select[name="weighting_method"]').value;
    
    // 1. Sembunyikan SEMUA opsi dulu
    document.querySelectorAll('.method-option').forEach(el => el.style.display = 'none');
    
    // Ambil div default (placeholder)
    const defaultDiv = document.getElementById('opt_default');
    if(defaultDiv) defaultDiv.style.display = 'none';

    let hasSpecificSettings = false;

    // 2. Cek Ranking Method
    if (rankMethod === 'topsis') {
        document.getElementById('opt_topsis').style.display = 'block';
        hasSpecificSettings = true;
    } else if (rankMethod === 'promethee') {
        const promDiv = document.getElementById('opt_promethee');
        promDiv.style.display = 'block';
        hasSpecificSettings = true;
        updatePrometheeInputs(); // Panggil fungsi update input p/q/s
    }

    // 3. Cek Weighting Method
    if (weightMethod === 'ahp') {
        document.getElementById('opt_ahp').style.display = 'block';
        hasSpecificSettings = true;
    }

    // 4. Jika TIDAK ADA setting khusus (misal: SAW + Direct), tampilkan Placeholder
    if (!hasSpecificSettings && defaultDiv) {
        defaultDiv.style.display = 'block';
    }
}

function updatePrometheeInputs() {
    const type = document.getElementById('prom_pref_select').value;
    const boxQ = document.getElementById('box_q'), boxP = document.getElementById('box_p'), boxS = document.getElementById('box_s');
    boxQ.style.display = boxP.style.display = boxS.style.display = 'none';

    if (type === 'ushape') boxQ.style.display = 'block';
    else if (type === 'vshape') boxP.style.display = 'block';
    else if (type === 'level' || type === 'linear') { boxQ.style.display = 'block'; boxP.style.display = 'block'; }
    else if (type === 'gaussian') boxS.style.display = 'block';
}

/* ================= 4. HALAMAN AHP ================= */
function initAhpPage() {
    window.updateLabel = function(input, labelId) {
        const val = parseInt(input.value);
        const label = document.getElementById(labelId);
        if (val === 0) { label.innerHTML = "Sama Penting (1)"; label.className = "small text-muted mt-1 fw-bold"; }
        else if (val < 0) { label.innerHTML = "⬅️ Kiri Lebih Penting (" + Math.abs(val) + ")"; label.className = "small text-primary mt-1 fw-bold"; }
        else { label.innerHTML = "Kanan Lebih Penting (" + val + ") ➡️"; label.className = "small text-success mt-1 fw-bold"; }
    };
}

/* ================= 5. HALAMAN RESULT ================= */
function initResultPage() {
    if(!window.PAGE_DATA || !window.PAGE_DATA.chartData) return;
    const ctx = document.getElementById('radarChart').getContext('2d');
    new Chart(ctx, {
        type: 'radar',
        data: window.PAGE_DATA.chartData,
        options: {
            responsive: true, maintainAspectRatio: false,
            scales: { r: { suggestedMin: 0, suggestedMax: 1, ticks: { display: false } } },
            plugins: { legend: { position: 'bottom' } }
        }
    });
}

/* ================= 6. HALAMAN ANALYSIS ================= */
function initAnalysisPage() {
    if(!window.ANALYSIS_DATA) return;
    const D = window.ANALYSIS_DATA;
    
    // Init Dropdowns
    const selA = document.getElementById('selectA'), selB = document.getElementById('selectB');
    Object.keys(D.rawData).forEach((alt, i) => {
        selA.add(new Option(alt, alt, false, i===0)); selB.add(new Option(alt, alt, false, i===1));
    });

    const m1 = document.getElementById('method1'), m2 = document.getElementById('method2');
    m2.add(new Option("-- Pilih --", "", true, true)); m2.options[0].disabled = true;
    Object.keys(D.methodsData).forEach(m => {
        m1.add(new Option(m, m, false, m === D.currentMethod)); m2.add(new Option(m, m));
    });

    // Sensitivity Logic
    const ctxLive = document.getElementById('liveChart').getContext('2d');
    let liveChart = new Chart(ctxLive, { type: 'bar', data: {labels:[], datasets:[]}, options: {responsive:true, maintainAspectRatio:false} });
    const sliders = document.querySelectorAll('.weight-slider');
    let debounceTimer;

    sliders.forEach(s => {
        s.dataset.prevValue = s.value;
        s.addEventListener('input', function() {
            // (Logika slider disederhanakan agar tidak infinite loop)
            document.getElementById('badge_'+this.name).innerText = parseFloat(this.value).toFixed(1)+'%';
            clearTimeout(debounceTimer); 
            debounceTimer = setTimeout(sendSensitivity, 150);
        });
    });

    function sendSensitivity() {
        let raw = {}; sliders.forEach(s => raw[s.name] = parseFloat(s.value));
        fetch(D.apiUrl, { method:"POST", headers:{'Content-Type':'application/json'}, body:JSON.stringify(raw) })
        .then(r=>r.json()).then(d=>{
            document.getElementById('liveTableContainer').innerHTML = d.html_table;
            liveChart.data = d.chart_data; liveChart.update();
        });
    }

    // Comparison Logic
    window.updateHeadToHead = function() {
        const altA = document.getElementById('selectA').value, altB = document.getElementById('selectB').value;
        const criteria = Object.keys(D.criteriaType);
        document.getElementById('thA').innerText = altA; document.getElementById('thB').innerText = altB;
        let html = '';
        
        criteria.forEach(c => {
            const vA = D.rawData[altA][c], vB = D.rawData[altB][c], diff = vA-vB;
            const isCost = D.criteriaType[c] === 'cost';
            const color = diff !== 0 ? (isCost ? (diff < 0 ? 'text-success':'text-danger') : (diff > 0 ? 'text-success':'text-danger')) : 'text-muted';
            html += `<tr><td>${c}</td><td>${vA}</td><td>${vB}</td><td class="${color} fw-bold">${diff !== 0 ? (diff>0?'▲':'▼') : '='} ${Math.abs(diff)}</td></tr>`;
        });
        document.getElementById('compareBody').innerHTML = html;
    };

    window.updateMethodComparison = function() {
        const m1 = document.getElementById('method1').value, m2 = document.getElementById('method2').value;
        if(!m2) return;
        let html = '';
        Object.keys(D.rawData).forEach(alt => {
            const r1 = D.methodsData[m1][alt], r2 = D.methodsData[m2][alt];
            const same = r1.Rank === r2.Rank;
            html += `<tr><td class="fw-bold">${alt}</td><td>#${r1.Rank}</td><td>#${r2.Rank}</td><td class="${same?'text-success':'text-warning'}">${same?'✅':'⚠️'}</td></tr>`;
        });
        document.getElementById('methodBody').innerHTML = html;
    };

    // Trigger Awal
    sendSensitivity(); updateHeadToHead();
    document.getElementById('selectA').addEventListener('change', updateHeadToHead);
    document.getElementById('selectB').addEventListener('change', updateHeadToHead);
    document.getElementById('method1').addEventListener('change', updateMethodComparison);
    document.getElementById('method2').addEventListener('change', updateMethodComparison);
}