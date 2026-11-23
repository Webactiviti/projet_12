import numpy as np
import scipy.signal as signal
from lib import bandpass_filter, notch_filter

def compute_snr(freqs, psd, band_low=3, band_high=30):
    """
    Calcule le SNR (Signal-to-Noise Ratio) en dB.
    Signal = puissance dans la bande utile (3-30 Hz)
    Noise = puissance hors de la bande utile
    """
    mask_signal = (freqs >= band_low) & (freqs <= band_high)
    mask_noise = ~mask_signal & (freqs > 0)  # Exclut la composante DC à 0Hz

    power_signal = np.sum(psd[mask_signal])
    power_noise = np.sum(psd[mask_noise])

    if power_noise == 0 or np.isnan(power_noise):
        return 0.0

    snr_db = 10 * np.log10(power_signal / power_noise)
    return float(snr_db)

def get_power_at_freq(freqs, psd, target_freq):
    """Retourne l'amplitude spectrale (PSD) la plus proche de la fréquence cible."""
    idx = np.argmin(np.abs(freqs - target_freq))
    return float(psd[idx])

def calculer_et_sauvegarder_resultats(db_conn, id_position, chan_label, raw_signal, sfreq):
    """
    Calcule les métriques EEG (offset_eeg, amplitude brute, amplitude filtrée 3-30Hz, SNR, etc.)
    et les insère dans la table result_EEG de DuckDB.
    """
    # 1. Calculs sur le signal BRUT
    offset_eeg = float(np.mean(raw_signal))
    raw_amplitude = float(np.max(raw_signal) - np.min(raw_signal))

    # 2. Filtrage rigoureux aligné sur la bande d'intérêt (3-30 Hz + Notch 50Hz)
    filtered_signal = bandpass_filter(raw_signal, sfreq, low=3, high=30)
    filtered_signal = notch_filter(filtered_signal, sfreq, freq=50)

    # 3. Calcul de l'amplitude EEG sur le signal filtré (3-30 Hz)
    # Option robuste : Utilisation des percentiles (95e - 5e) pour écarter les micro-artefacts transitoires,
    # tout en conservant une excellente fidélité par rapport à l'activité visible sur le scalogramme.
    p95 = np.percentile(filtered_signal, 95)
    p5 = np.percentile(filtered_signal, 5)
    eeg_amplitude = float(p95 - p5)
    
    # (Alternative classique si vous préférez le max-min pur sur le filtré : 
    # eeg_amplitude = float(np.max(filtered_signal) - np.min(filtered_signal)))

    # 4. Calcul du spectre FFT (via Welch) pour 50Hz, 60Hz et SNR
    nperseg = min(4 * sfreq, len(raw_signal))
    fft_freqs, psd = signal.welch(raw_signal, fs=sfreq, nperseg=nperseg)

    max_50Hz = get_power_at_freq(fft_freqs, psd, 50.0)
    max_60Hz = get_power_at_freq(fft_freqs, psd, 60.0)
    snr = compute_snr(fft_freqs, psd, band_low=3, band_high=30)
    ratio_rank = 0

    # 5. Enregistrement en base de données DuckDB
    db_conn.execute("""
        INSERT INTO result_EEG (
            id_position, capteur, offset_eeg, raw_amplitude, 
            eeg_amplitude, max_50Hz, max_60Hz, snr, ratio_rank
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        id_position, chan_label, offset_eeg, raw_amplitude,
        eeg_amplitude, max_50Hz, max_60Hz, snr, ratio_rank
    ))

    print(f"  [RESULT] Métriques 3-30Hz validées pour {chan_label} (Amplitude EEG: {eeg_amplitude:.2f} µV, SNR: {snr:.2f} dB)")
