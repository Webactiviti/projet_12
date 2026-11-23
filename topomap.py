import os
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Forçage du mode non-interactif
import matplotlib.pyplot as plt
import mne

from config import SessionConfig

def generer_et_sauvegarder_topomaps(db_conn, eeg_data_filtered, sfreq, channel_labels, marker_times_relative, marker_labels, cfg ):

 
    """
    Génère des topomaps par fenêtre glissante (fenêtre de 2s, pas de 0.5s),
    associe un id_position existant (en partant de 1 et en s'incrémentant en Python),
    vérifie son existence dans positionEEG, et stocke les références dans DuckDB.
    """
 

    # Paramètres de la fenêtre glissante
    window_duration = 2.0  # Durée de la fenêtre en secondes
    step_duration = 0.5    # Pas d'incrémentation en secondes

    samples_per_window = int(sfreq * window_duration)
    step_samples = int(sfreq * step_duration)

    total_samples = eeg_data_filtered.shape[1]
    n_windows = max(0, (total_samples - samples_per_window) // step_samples + 1)

    print(f"➡️ Génération de {n_windows} topomaps glissantes (pas de {step_duration}s) ")

    # Configuration du montage MNE standard 10-20
    montage = mne.channels.make_standard_montage("colin27_1020")
    info = mne.create_info(ch_names=channel_labels, sfreq=sfreq, ch_types="eeg")
    info.set_montage(montage)

    # Nettoyage préalable des anciennes entrées topomap dans DuckDB
    db_conn.execute("DELETE FROM grapheTopomap;")



    for i in range(n_windows):
        start_idx = i * step_samples
        end_idx = start_idx + samples_per_window

        t_start = start_idx / sfreq
        t_end = end_idx / sfreq



        # Extraction et moyennage du segment pour la topomap
        segment = eeg_data_filtered[:, start_idx:end_idx]
        data_avg = segment.mean(axis=1)

        # --- Gestion des marqueurs temporels ---
        markers_in_window = []
        if len(marker_times_relative) > 0:
            for m_time, m_label in zip(marker_times_relative, marker_labels):
                if t_start <= m_time < t_end:
                    markers_in_window.append((m_time, m_label))

        marker_str = ""
        if len(markers_in_window) > 0:
            labels_text = " | ".join([lbl for _, lbl in markers_in_window])
            marker_str = f" | Marker: {labels_text}"

        # --- Création de la figure ---
        fig, ax = plt.subplots(figsize=(4, 4), dpi=150)
        
        mne.viz.plot_topomap(
            data_avg,
            info,
            axes=ax,
            show=False,
            contours=0,
            cmap='RdBu_r',
            sphere=0.1,
            outlines='head'
        )

        ax.set_title(f"[{t_start:.1f}s – {t_end:.1f}s]{marker_str}", fontsize=7, fontweight='bold')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_aspect('equal')

        # Nom du fichier et sauvegarde au format WebP
        img_filename = f"topomap_{i+1}.webp"
        img_path = os.path.join(cfg.temp_dir_topomap, img_filename)
        
        fig.savefig(img_path, format="webp", pil_kwargs={"quality": 90}, bbox_inches='tight')
        plt.close(fig)

        # --- Enregistrement de la référence dans DuckDB avec l'id_position courant ---
        db_conn.execute("""
            INSERT INTO grapheTopomap (nom_graphe,  temps_debut, temps_fin)
            VALUES (?, ?,  ?)
        """, (img_filename,  t_start, t_end))



    print(f"✅ {n_windows} topomaps générées et enregistrées en BDD avec succès .")
