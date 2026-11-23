import os
import matplotlib.pyplot as plt
from lib import bandpass_filter, notch_filter, compute_fft
from config import SessionConfig


#def traiter_et_sauvegarder_fft(db_conn, id_position, chan_label, raw_signal, sfreq, temp_dir="tmp"):
def traiter_et_sauvegarder_fft(db_conn, id_position, chan_label, raw_signal, sfreq, cfg : SessionConfig  ):


    # 1. Filtrage
    filtered = bandpass_filter(raw_signal, sfreq)
    filtered = notch_filter(filtered, sfreq)

    # 2. Calcul FFT / Welch
    fft_freqs, psd = compute_fft(filtered, sfreq)

    # 3. Tracé du graphique
    fig, ax = plt.subplots(figsize=(8, 3.5), dpi=150)


    mask = (fft_freqs >= 1) & (fft_freqs <= 30)

    ax.plot(fft_freqs[mask], psd[mask], color='#2980b9', linewidth=0.5)

    ax.set_ylim(0,100)

    ax.fill_between(fft_freqs[mask], psd[mask], color='#3498db', alpha=0.3)
    
    ax.set_title(f"Spectre FFT (Welch) - {chan_label}", fontsize=10, fontweight='bold')
    ax.set_xlabel("Fréquence (Hz)")
    ax.set_ylabel("Densité (µV²/Hz)")
    ax.grid(True, linestyle='--', alpha=0.5)

    # 4. Enregistrement de l'image
    filename = f"{chan_label}_FFT.webp"
    filepath = os.path.join(cfg.temp_dir_img, filename)
    fig.savefig(filepath, format="webp", pil_kwargs={"quality": 90}, bbox_inches='tight')
    plt.close(fig)




    # 5. Enregistrement en BDD DuckDB
    db_conn.execute("""
        INSERT INTO grapheFFT (nom_graphe, id_position)
        VALUES (?, ?)
    """, (filename, id_position))
    
    #print(f"  [FFT] Image sauvegardée : {filename} (ID Position: {id_position})")
