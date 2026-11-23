import scipy.signal as signal
import jax
import jax.numpy as jnp
from functools import partial

# --- Filtres de signal ---

def bandpass_filter(data, fs, low=3, high=30):
    """Filtre passe-bande Butterworth (3 - 30 Hz par défaut)."""
    sos = signal.butter(4, [low, high], btype='bandpass', fs=fs, output='sos')
    return signal.sosfiltfilt(sos, data)

def notch_filter(data, fs, freq=50, q=12.5):
    """Filtre coupe-bande (Notch) à 50 Hz."""
    b, a = signal.iirnotch(freq, q, fs)
    return signal.filtfilt(b, a, data)

def compute_fft(data, fs):
    """Calcule la Densité Spectrale de Puissance (PSD) via la méthode de Welch."""
    nperseg = min(2 * fs, len(data))
    freqs, psd = signal.welch(data, fs=fs, nperseg=nperseg)
    return freqs, psd

# --- Transformation par Ondelette de Morlet (JAX) ---

def get_bc(cycles, freq, k_sd=5):
    return cycles / (k_sd * freq)

def cxmorelet(freq, cycles, sampling_freq):
    t = jnp.linspace(-1, 1, sampling_freq * 2)
    bc = get_bc(cycles, freq)
    norm = 1 / (bc * jnp.sqrt(2 * jnp.pi))
    gauss = jnp.exp(-t**2 / (2 * bc**2))
    sine = jnp.exp(1j * 2 * jnp.pi * freq * t)
    wavelet = norm * gauss * sine
    return wavelet / jnp.sum(jnp.abs(wavelet))

@partial(jax.jit, static_argnums=3)
@partial(jax.vmap, in_axes=(None, 0, None, None))
def wavelet_transform(signal_data, freq, cycles, sampling_freq):
    wavelet = cxmorelet(freq, cycles, sampling_freq)
    return jax.scipy.signal.convolve(signal_data, wavelet, mode="same")