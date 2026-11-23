import os
import matplotlib
matplotlib.use('Agg')  # Forçage du mode non-interactif
import matplotlib.pyplot as plt
import numpy as np
from lib import bandpass_filter, notch_filter
from config import SessionConfig

def traiter_et_sauvegarder_courbe_eeg(db_conn, id_position, chan_label, raw_signal, sfreq, marker_times_rel, marker_labels, cfg : SessionConfig):


    """
    Filtre le signal brut, trace la courbe temporelle de l'EEG avec les marqueurs,
    sauvegarde l'image en WebP et enregistre sa référence dans la table grapheEEG de DuckDB.
    """

    # 1. Filtrage (bandpass 3-30Hz + notch 50Hz)
    filtered = bandpass_filter(raw_signal, sfreq, low=3, high=30)
    filtered = notch_filter(filtered, sfreq, freq=50)

    # Axe temporel en secondes
    time_axis = np.linspace(0, len(raw_signal) / sfreq, len(raw_signal))

    # 2. Tracé du graphique temporel
    fig, ax = plt.subplots(figsize=(8, 3.5), dpi=150)

    ax.set_ylim(-100,100)
    
    ax.plot(time_axis, filtered, color='#0284c7', linewidth=0.8, label=f'EEG {chan_label}')

    # 3. Ajout des marqueurs temporels (traits verticaux en pointillés)
    for t, label in zip(marker_times_rel, marker_labels):
        if 0 <= t <= time_axis[-1]:
            ax.axvline(x=t, color='#ef4444', linestyle='--', linewidth=1)
            ax.text(
                t, -90, label, color='#991b1b', fontsize=6,
                ha='left', va='top',
                bbox=dict(facecolor='#fee2e2', edgecolor='#fca5a5', boxstyle='round,pad=0.2', alpha=0.8)
            )
            ax.set_ylim(-100,100)

    ax.set_title(f"Courbe EEG Filtrée (3-30 Hz) - {chan_label}", fontsize=10, fontweight='bold')
    ax.set_xlabel("Temps (s)", fontsize=9)
    ax.set_ylabel("Amplitude (µV)", fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.4)
    ax.legend(loc='upper right', fontsize=8)

    # 4. Sauvegarde de l'image au format WebP (optimisé)
    filename = f"{chan_label}_EEG.webp"
    filepath = os.path.join(cfg.temp_dir_img, filename)
    fig.savefig(filepath, format="webp", pil_kwargs={"quality": 90}, bbox_inches='tight')
    plt.close(fig)

    # 5. Enregistrement de la référence dans la table 'grapheEEG' de DuckDB
    db_conn.execute("""
        INSERT INTO grapheEEG (nom_graphe, id_position)
        VALUES (?, ?)
    """, (filename, id_position))

    #print(f"  [COURBE EEG] Image sauvegardée : {filename} (ID Position: {id_position})")
