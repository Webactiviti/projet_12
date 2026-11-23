import os
import json
from datetime import datetime
import duckdb
from weasyprint import HTML
from config import SessionConfig



def generer_rapport_html(cfg : SessionConfig , inclure_topomap=True):


    if not os.path.exists(cfg.db_path):
        raise FileNotFoundError(f"Base de données introuvable : {db_path}")

    conn = duckdb.connect(cfg.db_path)
    date_jour = datetime.now().strftime("%d/%m/%Y")

    # 1. Récupération des données du tableau result_EEG jointes à positionEEG
    df_results = conn.execute("""
        SELECT 
            p.nom_position AS "Position",
            ROUND(r.offset_eeg, 2) AS "Offset (µV)",
            ROUND(r.raw_amplitude, 2) AS "Amplitude Brute (µV)",
            ROUND(r.eeg_amplitude, 2) AS "Amplitude EEG 3-30Hz (µV)",
            ROUND(r.max_50Hz, 4) AS "Pic 50Hz (µV²/Hz)",
            ROUND(r.snr, 2) AS "SNR (dB)",
            r.ratio_rank AS "Ratio rank"
        FROM positionEEG p
        INNER JOIN result_EEG r ON p.id = r.id_position
        ORDER BY p.id
    """).fetchdf()

    # 2. Récupération des graphiques EEG, FFT, Énergie et SCA regroupés par positionEEG
    df_graphes = conn.execute("""
        SELECT 
            p.id,
            p.nom_position,
            g.nom_graphe AS eeg_file,
            f.nom_graphe AS fft_file,
            e.nom_graphe AS energy_file,
            s.nom_graphe AS sca_file
        FROM positionEEG p
        LEFT JOIN grapheEEG g ON p.id = g.id_position
        LEFT JOIN grapheFFT f ON p.id = f.id_position
        LEFT JOIN energie e ON p.id = e.id_position
        LEFT JOIN grapheSCA s ON p.id = s.id_position
        ORDER BY p.id
    """).fetchdf()

    # 3. Récupération ordonnée des fichiers Topomap depuis DuckDB
    rows_topomap = []
    if inclure_topomap:
        rows_topomap = conn.execute("""
            SELECT nom_graphe
            FROM grapheTopomap
            ORDER BY id ASC
        """).fetchall()

    df_identifiant = conn.execute("SELECT nom_identifiant from identifiant").fetchdf()

    # Récupération fichier head depuis DuckDB
    result_head_img = conn.execute("SELECT img_head FROM grapheHead").fetchone()
    head_img_path_relatif = os.path.basename(result_head_img[0]) if result_head_img and result_head_img[0] else ""
    

    pos_identifiant = ""
    for _, row in df_identifiant.iterrows():
        pos_identifiant = row["nom_identifiant"]

    conn.close()

    # Vérification physique des fichiers Topomap dans temp/topomap/
    topomap_files = []
    if inclure_topomap:
        topomap_dir = cfg.temp_dir_topomap 
        for (nom_fichier,) in rows_topomap:
            chemin_physique = os.path.join(topomap_dir, nom_fichier)
            if os.path.exists(chemin_physique):
                # Pour le ZIP, on garde le préfixe topomap/
                topomap_files.append(f"topomap/{nom_fichier}")

    # Construction du tableau HTML pour result_EEG
    table_headers = "".join(f"<th>{col}</th>" for col in df_results.columns)
    table_rows = ""
    for _, row in df_results.iterrows():
        cells = "".join(f"<td>{val}</td>" for val in row)
        table_rows += f"<tr>{cells}</tr>\n"

    # Construction des blocs graphiques regroupés par position
    positions_html = ""
    for _, row in df_graphes.iterrows():
        pos_name = row["nom_position"]
        graphes_a_afficher = [
            ("Courbe EEG Filtrée (3-30 Hz)", row["eeg_file"]), 
            ("Spectre FFT (Welch)", row["fft_file"]),
            ("Énergie Relative (Theta / Alpha / Beta)", row["energy_file"]),
            ("Scalogramme (Ondelettes de Morlet)", row["sca_file"]),
        ]

        cards_html = ""
        for titre_graphe, filename in graphes_a_afficher:
            if filename and isinstance(filename, str):
                # On extrait uniquement le nom du fichier pour que base_url fonctionne parfaitement
                nom_base_fic = os.path.basename(filename)
                filepath_check = os.path.join(cfg.temp_dir_img, nom_base_fic)
                
                if os.path.exists(filepath_check):
                    cards_html += f"""
                        <div class="graph-card">
                            <h4>{titre_graphe}</h4>
                            <img src="{nom_base_fic}" alt="{titre_graphe} - {pos_name}" title="Double-cliquez pour afficher en plein écran" loading="lazy" ondblclick="!document.fullscreenElement ? this.requestFullscreen() : document.exitFullscreen();" />
                        </div>
                    """
                else:
                    cards_html += f"""
                    <div class="graph-card missing">
                        <h4>{titre_graphe}</h4>
                        <p>⚠️ Fichier introuvable : <code>{filepath_check}</code></p>
                    </div>
                    """

        if cards_html:
            positions_html += f"""
            <section class="position-block">
                <h3>Position : {pos_name}</h3>
                <div class="graphs-grid">
                    {cards_html}
                </div>
            </section>
            """

    # Construction de la section Topomap
    if inclure_topomap:
        if topomap_files:
            topomap_section_html = f"""
            <section>
                <h2>Animation Topographique (Fenêtres glissantes)</h2>
                <div class="position-block topomap-block">
                    <h3>Évolution spatiale globale (2s / pas de 0.5s)</h3>
                    <div class="tm-controls">
                        <div class="tm-nav-group">
                            <button type="button" class="tm-btn tm-btn-secondary" id="tm-prevBtn"><span>&#9664;</span> Précédent</button>
                            <button type="button" class="tm-btn tm-btn-primary" id="tm-playPauseBtn"><span>&#9654;</span> Lecture</button>
                            <button type="button" class="tm-btn tm-btn-secondary" id="tm-nextBtn">Suivant <span>&#9654;</span></button>
                        </div>
                        <div class="tm-settings-group">
                            <label class="tm-label" for="tm-interval">Intervalle (ms)<input id="tm-interval" type="number" value="500" min="50" step="50" /></label>
                            <label class="tm-checkbox-label"><input id="tm-autoPlay" type="checkbox" /><span>Lecture auto</span></label>
                        </div>
                    </div>
                    <div class="graph-card tm-stage-card">
                        <div class="tm-badge" id="tm-badge">Image -- / --</div>
                        <img id="tm-slide" src="" alt="Topomap" title="Double-cliquez pour afficher en plein écran" />
                        <div class="tm-tip">Astuce : flèches ◀ ▶ pour naviguer • barre espace pour lecture/pause</div>
                    </div>
                </div>
            </section>
            """
        else:
            topomap_section_html = """
            <section>
                <h2>Animation Topographique</h2>
                <div class="position-block">
                    <div class="graph-card missing"><p>⚠️ Aucune image topomap trouvée.</p></div>
                </div>
            </section>
            """
    else:
        topomap_section_html = ""

    html_content = f"""<!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Rapport EEG OPEN / CLOSE - {date_jour}</title>
        <style>
            /* Configuration de la page pour WeasyPrint (Format A4 Paysage pour tout faire tenir sans coupure) */
            @page {{
                size: A4 landscape;
                margin:  10mm; 

                /* Définition du pied de page en bas à droite */
                @bottom-right {{
                    content: "Rapport EEG  page : " counter(page) " / " counter(pages);
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    font-size: 8.5pt;
                    color: #64748b; /* Gris élégant */
                }}
            }}

            :root {{
                --primary: #1e293b;
                --accent: #2563eb;
                --accent-hover: #1d4ed8;
                --bg: #f8fafc;
                --card-bg: #ffffff;
                --subtle-bg: #f1f5f9;
                --border: #e2e8f0;
                --text: #334155;
                --text-muted: #64748b;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background-color: var(--bg);
                color: var(--text);
                margin: 0;
                padding: 10px;
                line-height: 1.5;
            }}
            .container {{
                width: 100%;
                max-width: none;
                margin: 0 auto;
            }}
            header.report-header {{
                background: var(--primary);
                color: #ffffff;
                padding: 20px 25px;
                border-radius: 10px;
                margin-bottom: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                page-break-inside: avoid;
                break-inside: avoid;
            }}
            header.report-header h1 {{
                margin: 0;
                font-size: 1.5rem;
                letter-spacing: 0.5px;
            }}
            .date-badge, .did-badge {{
                background: rgba(255, 255, 255, 0.15);
                padding: 6px 14px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 0.95rem;
            }}
            h2 {{
                color: var(--primary);
                border-bottom: 2px solid var(--accent);
                padding-bottom: 6px;
                margin-top: 25px;
                margin-bottom: 15px;
                font-size: 1.2rem;
                page-break-after: avoid;
                break-after: avoid;
            }}

            /* Tableau result_EEG */
            .table-wrapper {{
                background: var(--card-bg);
                border-radius: 10px;
                border: 1px solid var(--border);
                overflow-x: auto;
                margin-bottom: 25px;
                page-break-inside: avoid;
                break-inside: avoid;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 0.85rem;
                text-align: right;
            }}
            th, td {{
                padding: 10px 12px;
                border-bottom: 1px solid var(--border);
            }}
            th {{
                background-color: var(--subtle-bg);
                color: var(--primary);
                font-weight: 600;
                white-space: nowrap;
            }}
            th:first-child, td:first-child,
            th:nth-child(2), td:nth-child(2) {{
                text-align: left;
                font-weight: 600;
            }}

            /* Blocs conteneurs (Positions & Topomap) */
            .position-block {{
                background: var(--card-bg);
                border: 1px solid var(--border);
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 20px;
                page-break-inside: avoid;
                break-inside: avoid;
            }}
            .position-block h3 {{
                margin-top: 0;
                margin-bottom: 12px;
                color: var(--accent);
                font-size: 1.1rem;
                border-left: 4px solid var(--accent);
                padding-left: 10px;
            }}
            .graphs-grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr); /* Force 2 colonnes bien nettes en PDF paysage */
                gap: 15px;
            }}
            .graph-card {{
                border: 1px solid var(--border);
                border-radius: 8px;
                padding: 10px;
                background: var(--card-bg);
                text-align: center;
                page-break-inside: avoid;
                break-inside: avoid;
            }}
            .graph-card h4 {{
                margin: 0 0 8px 0;
                font-size: 0.85rem;
                color: var(--primary);
            }}
            .graph-card img {{
                width: 100%;
                height: auto;
                max-height: 220px;
                object-fit: contain;
                border-radius: 4px;
            }}
            .graph-card.missing {{
                background-color: #fef2f2;
                border-color: #fecaca;
                color: #991b1b;
                display: flex;
                flex-direction: column;
                justify-content: center;
                min-height: 120px;
            }}

            .section-tete {{
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 25px;
                display: flex;
                flex-direction: column;
                align-items: center;
                page-break-inside: avoid;
                break-inside: avoid;
            }}
            .section-tete h2 {{
                font-size: 1.15rem;
                color: #0f172a;
                margin-top: 0;
                margin-bottom: 12px;
                border-bottom: 2px solid #f1f5f9;
                width: 100%;
                padding-bottom: 8px;
                text-align: center;
            }}
            .graph-container {{
                position: relative;
                background: #f8fafc;
                border-radius: 8px;
                padding: 8px;
                border: 1px solid #f1f5f9;
                display: inline-block;
                text-align: center;
            }}
            img.interactive-graph {{
                max-width: 250px;
                height: auto;
            }}

            /* Masquage des éléments interactifs inutiles sur le PDF papier */
            @media print {{
                body {{ background: #ffffff; padding: 0; }}
                .tm-controls, .tm-tip {{ display: none; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header class="report-header">
                <h1>Rapport EEG OPEN / CLOSE</h1>
                <div class="did-badge">ID : {pos_identifiant}</div>
                <div class="date-badge">Date : {date_jour}</div>
            </header>

            <div class="section-tete">
                <h2>Configuration des Électrodes (Tête)</h2>
                <div class="graph-container">
                    <img src="{head_img_path_relatif}" alt="Cartographie Tête" class="interactive-graph">
                </div>
            </div>

            <section>
                <h2>Synthèse des métriques (result_EEG)</h2>
                <div class="table-wrapper">
                    <table>
                        <thead><tr>{table_headers}</tr></thead>
                        <tbody>{table_rows}</tbody>
                    </table>
                </div>
            </section>

            <section>
                <h2>Analyse fréquentielle et temps-fréquence par position</h2>
                {positions_html}
            </section>

            {topomap_section_html}
        </div>

    <script>
    const tmFiles = {json.dumps(topomap_files, indent=2)};
    if (tmFiles.length > 0) {{
        let tmIndex = 0;
        const tmImg = document.getElementById('tm-slide');
        const tmBadge = document.getElementById('tm-badge');
        const tmIntervalInput = document.getElementById('tm-interval');
        const tmAutoPlay = document.getElementById('tm-autoPlay');
        const tmPlayPauseBtn = document.getElementById('tm-playPauseBtn');
        let tmTimer = null;

        function tmShow(index) {{
            tmIndex = (index + tmFiles.length) % tmFiles.length;
            tmImg.src = tmFiles[tmIndex];
            tmBadge.textContent = "Fenêtre " + (tmIndex + 1) + " / " + tmFiles.length;
        }}
        function tmPlay() {{
            tmStop();
            const iv = Math.max(50, Number(tmIntervalInput.value) || 500);
            tmTimer = setInterval(() => tmShow(tmIndex + 1), iv);
            tmPlayPauseBtn.innerHTML = "<span>&#10074;&#10074;</span> Pause";
        }}
        function tmStop() {{
            if (tmTimer) {{ clearInterval(tmTimer); tmTimer = null; }}
            tmPlayPauseBtn.innerHTML = "<span>&#9654;</span> Lecture";
        }}
        function tmToggle() {{ tmTimer ? tmStop() : tmPlay(); }}

        document.getElementById('tm-nextBtn').onclick = () => {{ tmStop(); tmShow(tmIndex + 1); }};
        document.getElementById('tm-prevBtn').onclick = () => {{ tmStop(); tmShow(tmIndex - 1); }};
        tmPlayPauseBtn.onclick = tmToggle;
        tmIntervalInput.onchange = () => {{ if (tmAutoPlay.checked) tmPlay(); }};
        tmAutoPlay.onchange = () => {{ tmAutoPlay.checked ? tmPlay() : tmStop(); }};

        window.addEventListener('keydown', (e) => {{
            if (document.activeElement === tmIntervalInput) return;
            if (e.code === "ArrowRight") {{ tmStop(); tmShow(tmIndex + 1); }}
            else if (e.code === "ArrowLeft") {{ tmStop(); tmShow(tmIndex - 1); }}
            else if (e.code === "Space") {{ e.preventDefault(); tmToggle(); }}
        }});

        tmImg.ondblclick = () => {{
            !document.fullscreenElement ? tmImg.requestFullscreen() : document.exitFullscreen();
        }};
        tmShow(0);
        if (tmAutoPlay.checked) tmPlay();
    }}
    </script>
    </body>
    </html>
    """

    if inclure_topomap:
        filename_path = os.path.join(cfg.temp_dir_img, "rapport_eeg.html")
        with open(filename_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"✅ Rapport HTML généré avec succès :  (Topomaps incluses)")
    else:
        # Génération du PDF via WeasyPrint avec base_url pointant sur le dossier des images
        filename_path = os.path.join(cfg.temp_dir_img, "rapport_eeg.pdf")
        HTML(string=html_content, base_url=cfg.temp_dir_img).write_pdf(filename_path)
        print(f"✅ Rapport PDF généré avec succès ")



