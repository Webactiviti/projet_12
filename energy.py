import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from config import SessionConfig

def calculer_energie_bande(abs_scalogram, total_power, freqs, f_min, f_max):
    """Calcule l'énergie relative moyenne pour une bande de fréquence donnée."""
    mask = (freqs >= f_min) & (freqs <= f_max)
    band_power = np.sum(abs_scalogram[mask, :], axis=0)
    return band_power / total_power

def traiter_et_sauvegarder_energie(db_conn, id_position, chan_label, scalogram_np, freqs_np, sfreq, marker_times_rel, marker_labels, cfg: SessionConfig):
    # 1. Calcul de l'énergie relative en NumPy (sans recalculer les ondelettes)
    abs_scalo = np.abs(scalogram_np).astype(np.float32)
    total_power = np.sum(abs_scalo, axis=0) + 1e-12
    time_axis = np.linspace(0, scalogram_np.shape[1] / sfreq, scalogram_np.shape[1], dtype=np.float32)

    energy_theta = calculer_energie_bande(abs_scalo, total_power, freqs_np, 4.0, 8.0)
    energy_alpha = calculer_energie_bande(abs_scalo, total_power, freqs_np, 8.0, 13.0)
    energy_beta  = calculer_energie_bande(abs_scalo, total_power, freqs_np, 13.0, 30.0)

    del abs_scalo, total_power

    # 2. Tracé du graphique (figsize réduit de (18, 10) à (8, 3.5))
    fig, ax = plt.subplots(figsize=(8, 3.5), dpi=150)

    ax.plot(time_axis, energy_theta, color='green', label='Theta (4-8 Hz)', linewidth=0.8)
    ax.plot(time_axis, energy_alpha, color='red', label='Alpha (8-13 Hz)', linewidth=0.8)
    ax.plot(time_axis, energy_beta,  color='blue', label='Beta (13-30 Hz)', linewidth=0.8)

    # 3. Ajout des marqueurs temporels
    for t, label in zip(marker_times_rel, marker_labels):
        if 0 <= t <= time_axis[-1]:
            ax.axvline(x=t, color='gray', linestyle='--', linewidth=1)
            ax.text(
                t, 0.05, label, color='black', fontsize=6,
                ha='left', va='bottom',
                bbox=dict(facecolor='white', edgecolor='gray', boxstyle='round,pad=0.2', alpha=0.8)
            )

    ax.set_title(f"Énergie Relative (Theta, Alpha, Beta) - {chan_label}", fontsize=10, fontweight='bold')
    ax.set_xlabel("Temps (s)")
    ax.set_ylabel("Énergie Relative")
    ax.set_ylim(-0.05, 1.05)
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, linestyle='--', alpha=0.4)

    # 4. Sauvegarde de l'image
    filename = f"{chan_label}_energy.webp"
    filepath = os.path.join(cfg.temp_dir_img, filename)
    fig.savefig(filepath, format="webp", pil_kwargs={"quality": 85}, bbox_inches='tight')
    plt.close(fig)

    del energy_theta, energy_alpha, energy_beta, time_axis

    # 5. Enregistrement dans la table 'energie' de DuckDB
    db_conn.execute("""
        INSERT INTO energie (nom_graphe, id_position)
        VALUES (?, ?)
    """, (filename, id_position))