import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np
from config import SessionConfig

def traiter_et_sauvegarder_sca(db_conn, id_position, chan_label, scalogram_np, freqs_np, sfreq, marker_times_rel, marker_labels, cfg: SessionConfig):
    # 1. Puissance en float32 pour limiter la RAM
    power = np.abs(scalogram_np).astype(np.float32)
    duration = scalogram_np.shape[1] / sfreq

    # Palette de couleur
    jet_cmap = plt.colormaps.get_cmap('jet')
    jet_colors = jet_cmap(np.linspace(0, 1, 256))
    jet_colors[:70, 2] = 1.0
    custom_jet = ListedColormap(jet_colors)

    # 2. Tracé du scalogramme (interpolation bilinear au lieu de bicubic + 150 dpi)
    fig, ax = plt.subplots(figsize=(8, 3.5), dpi=150)
    img = ax.imshow(
        power, aspect='auto', cmap=custom_jet, interpolation="bilinear",
        origin="lower", extent=[0, duration, freqs_np[0], freqs_np[-1]],
        vmin=0, vmax=4
    )

    # Ajout des marqueurs
    for t, label in zip(marker_times_rel, marker_labels):
        if 0 <= t <= duration:
            ax.axvline(x=t, color='white', linestyle='--', linewidth=1)
            ax.text(
                t, freqs_np[0] + 0.5, label, color='white', fontsize=6,
                ha='left', va='bottom',
                bbox=dict(facecolor='gray', edgecolor='none', boxstyle='round,pad=0.2', alpha=0.7)
            )

    ax.set_title(f"Scalogramme - {chan_label}", fontsize=10, fontweight='bold')
    ax.set_xlabel("Temps (s)")
    ax.set_ylabel("Fréquence (Hz)")
    ax.set_yticks([5, 10, 15, 20, 25, 30])
    ax.axhline(10, color='white', linestyle='--', linewidth=0.5)
    cbar = plt.colorbar(img, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Puissance")

    # 3. Enregistrement de l'image
    filename = f"{chan_label}_SCA.webp"
    filepath = os.path.join(cfg.temp_dir_img, filename)
    fig.savefig(filepath, format="webp", pil_kwargs={"quality": 85}, bbox_inches='tight')
    plt.close(fig)

    del power, custom_jet, jet_colors, jet_cmap

    # 4. Enregistrement en BDD DuckDB
    db_conn.execute("""
        INSERT INTO grapheSCA (nom_graphe, id_position)
        VALUES (?, ?)
    """, (filename, id_position))