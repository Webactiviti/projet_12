import os
import matplotlib.pyplot as plt
import numpy as np
import jax.numpy as jnp
from lib import bandpass_filter, notch_filter, wavelet_transform
from config import SessionConfig

def calculer_energie_bande(scalogram, freqs, f_min, f_max):
    """Calcule l'énergie relative moyenne pour une bande de fréquence donnée."""
    mask = (freqs >= f_min) & (freqs <= f_max)
    # Puissance (carré de l'amplitude ou valeur absolue) dans la bande / Puissance totale
    band_power = jnp.sum(jnp.abs(scalogram[mask, :]), axis=0)
    total_power = jnp.sum(jnp.abs(scalogram), axis=0) + 1e-12
    return band_power / total_power

def traiter_et_sauvegarder_energie(db_conn, id_position, chan_label, raw_signal, sfreq, marker_times_rel, marker_labels, cfg : SessionConfig):


    # 1. Filtrage rigoureux (identique au scalogramme)
    filtered = bandpass_filter(raw_signal, sfreq)
    filtered = notch_filter(filtered, sfreq)
    signal_jax = jnp.array(filtered)

    # 2. Calcul du scalogramme via les ondelettes de Morlet
    freqs = jnp.linspace(1, 30, 141)
    cycles = 33
    scalogram = wavelet_transform(signal_jax, freqs, cycles, sfreq)

    # 3. Calcul de l'énergie relative pour Theta, Alpha et Beta
    time_axis = jnp.linspace(0, len(signal_jax) / sfreq, scalogram.shape[1])
    
    energy_theta = calculer_energie_bande(scalogram, freqs, 4.0, 8.0)
    energy_alpha = calculer_energie_bande(scalogram, freqs, 8.0, 13.0)
    energy_beta  = calculer_energie_bande(scalogram, freqs, 13.0, 30.0)

    # 4. Tracé du graphique des 3 courbes
    fig, ax = plt.subplots(figsize=(18, 10), dpi=300)
    
    ax.plot(time_axis, energy_theta, color='green', label='Theta (4-8 Hz)', linewidth=0.8)
    ax.plot(time_axis, energy_alpha, color='red', label='Alpha (8-13 Hz)', linewidth=0.8)
    ax.plot(time_axis, energy_beta,  color='blue', label='Beta (13-30 Hz)', linewidth=0.8)

    # 5. Ajout des marqueurs temporels 
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

    # 6. Sauvegarde de l'image au format WebP (optimisé)
    filename = f"{chan_label}_energy.webp"
    filepath = os.path.join(cfg.temp_dir_img, filename)
    fig.savefig(filepath, format="webp", pil_kwargs={"quality": 90}, bbox_inches='tight')
    plt.close(fig)





    # 7. Enregistrement dans la table 'energie' de DuckDB
    db_conn.execute("""
        INSERT INTO energie (nom_graphe, id_position)
        VALUES (?, ?)
    """, (filename, id_position))

    #print(f"  [ENERGY] Image sauvegardée : {filename} (ID Position: {id_position})")
