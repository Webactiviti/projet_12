import os
import pyxdf
import duckdb
import numpy as np


from fft import traiter_et_sauvegarder_fft
from sca import traiter_et_sauvegarder_sca
from energy import traiter_et_sauvegarder_energie
from EEG_result import calculer_et_sauvegarder_resultats
from topomap import generer_et_sauvegarder_topomaps
from lib import bandpass_filter, notch_filter
from courbe_eeg import traiter_et_sauvegarder_courbe_eeg  

from head import generer_et_sauvegarder_tete
from gene_html import generer_rapport_html

from config import SessionConfig



def init_environment_rapport (session_id):


    


    TEMP_DIR = "tmp"
    TEMP_DIR_SESSION = f"tmp/{session_id}"
    TEMP_DIR_TOPOMAP = f"tmp/{session_id}/images/topomap"
    TEMP_DIR_IMG = f"tmp/{session_id}/images"
    TEMP_DIR_DATA = f"tmp/{session_id}/data"
    DB_PATH = f"tmp/{session_id}/eeg_database.duckdb"
    TEMP_DIR_RAPPORT =f"tmp/{session_id}/images/rapport"

    #OUTPUT_HTML = os.path.join(TEMP_DIR_IMG, "rapport_eeg.html")

    cfg = SessionConfig(
        temp_dir = TEMP_DIR,   
        temp_dir_topomap = TEMP_DIR_TOPOMAP, 
        temp_dir_img = TEMP_DIR_IMG , 
        temp_dir_data = TEMP_DIR_DATA,
        db_path = DB_PATH , 
        xdf_file = "" , 
        temp_rapport = TEMP_DIR_RAPPORT,
        temp_session_id = TEMP_DIR_SESSION ,
        name_session = session_id
    )



    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
        print(f"Dossier {TEMP_DIR} créé.\n")

    if not os.path.exists(TEMP_DIR_SESSION):
        os.makedirs(TEMP_DIR_SESSION)
        print(f"Dossier {TEMP_DIR_SESSION} créé.\n")

    if not os.path.exists(TEMP_DIR_DATA):
        os.makedirs(TEMP_DIR_DATA)
        print(f"Dossier {TEMP_DIR_DATA} créé.\n")

    if not os.path.exists(TEMP_DIR_IMG):
        os.makedirs(TEMP_DIR_IMG)
        print(f"Dossier {TEMP_DIR_IMG} créé.\n")

    if not os.path.exists(TEMP_DIR_RAPPORT):
        os.makedirs(TEMP_DIR_RAPPORT)
        print(f"Dossier {TEMP_DIR_RAPPORT} créé.\n")

    if not os.path.exists(TEMP_DIR_TOPOMAP):
        os.makedirs(TEMP_DIR_TOPOMAP)
        print(f"Dossier {TEMP_DIR_TOPOMAP} créé.\n")

    return cfg


def init_database(cfg: SessionConfig):

    conn = duckdb.connect(cfg.db_path)
    
    # --- CORRECTIF : Supprimer d'abord les tables dépendantes (FK) avant positionEEG ---
    conn.execute("DROP TABLE IF EXISTS grapheTopomap;")
    conn.execute("DROP TABLE IF EXISTS energie;")
    conn.execute("DROP TABLE IF EXISTS grapheSCA;")
    conn.execute("DROP TABLE IF EXISTS grapheFFT;")
    conn.execute("DROP TABLE IF EXISTS grapheEEG;")     
    conn.execute("DROP TABLE IF EXISTS result_EEG;")
    conn.execute("DROP TABLE IF EXISTS grapheAsymetrie;")
    conn.execute("DROP TABLE IF EXISTS grapheEnveloppe;")
    conn.execute("DROP TABLE IF EXISTS identifiant;")
    conn.execute("DROP TABLE IF EXISTS positionEEG;")
    conn.execute("DROP TABLE IF EXISTS grapheHead;")

# --- Supprimer et recréer les séquences pour qu'elles repartent à 1 ---
    conn.execute("DROP SEQUENCE IF EXISTS seq_position_id;")
    conn.execute("DROP SEQUENCE IF EXISTS seq_fft_id;")
    conn.execute("DROP SEQUENCE IF EXISTS seq_sca_id;")
    conn.execute("DROP SEQUENCE IF EXISTS seq_eeg_id;")  
    conn.execute("DROP SEQUENCE IF EXISTS seq_result_id;")
    conn.execute("DROP SEQUENCE IF EXISTS seq_energy_id;")
    conn.execute("DROP SEQUENCE IF EXISTS seq_topomap_id;")
    conn.execute("DROP SEQUENCE IF EXISTS seq_enveloppe_id;")
    conn.execute("DROP SEQUENCE IF EXISTS seq_asymetrie_id;")
  

    # Séquences auto-incrémentées
    conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_position_id START 1;")
    conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_fft_id START 1;")
    conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_sca_id START 1;")
    conn.execute("CREATE SEQUENCE seq_eeg_id START 1;")  
    conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_result_id START 1;")
    conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_energy_id START 1;") 
    conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_topomap_id START 1;") 
    conn.execute("CREATE SEQUENCE seq_enveloppe_id START 1;")
    conn.execute("CREATE SEQUENCE seq_asymetrie_id START 1;")  


        # Table identifiant
    conn.execute("""
        CREATE TABLE identifiant (
            nom_identifiant VARCHAR NOT NULL
        );
    """)


    # Table head
    conn.execute("""
        CREATE TABLE grapheHead (
            img_head VARCHAR NOT NULL
        );
    """)

    # Table positionEEG
    conn.execute("""
        CREATE TABLE positionEEG (
            id INTEGER PRIMARY KEY DEFAULT nextval('seq_position_id'),
            nom_position VARCHAR NOT NULL
        );
    """)

    # Table result_EEG
    conn.execute("""
        CREATE TABLE result_EEG (
            id INTEGER PRIMARY KEY DEFAULT nextval('seq_result_id'),
            id_position INTEGER,
            capteur VARCHAR NOT NULL,
            offset_eeg DOUBLE,
            raw_amplitude DOUBLE,
            eeg_amplitude DOUBLE,
            max_50Hz DOUBLE,
            max_60Hz DOUBLE,
            snr DOUBLE,
            ratio_rank DOUBLE DEFAULT 0,
            FOREIGN KEY (id_position) REFERENCES positionEEG(id)
        );
    """)

    # Table grapheEEG 
    conn.execute("""
        CREATE TABLE grapheEEG (
            id INTEGER PRIMARY KEY DEFAULT nextval('seq_eeg_id'),
            nom_graphe VARCHAR NOT NULL,
            id_position INTEGER,
            FOREIGN KEY (id_position) REFERENCES positionEEG(id)
        );
    """)
    # Table grapheFFT
    conn.execute("""
        CREATE TABLE grapheFFT (
            id INTEGER PRIMARY KEY DEFAULT nextval('seq_fft_id'),
            nom_graphe VARCHAR NOT NULL,
            id_position INTEGER,
            FOREIGN KEY (id_position) REFERENCES positionEEG(id)
        );
    """)

    # Table grapheSCA
    conn.execute("""
        CREATE TABLE grapheSCA (
            id INTEGER PRIMARY KEY DEFAULT nextval('seq_sca_id'),
            nom_graphe VARCHAR NOT NULL,
            id_position INTEGER,
            FOREIGN KEY (id_position) REFERENCES positionEEG(id)
        );
    """)

    # Table energie
    conn.execute("""
        CREATE TABLE energie (
            id INTEGER PRIMARY KEY DEFAULT nextval('seq_energy_id'),
            nom_graphe VARCHAR NOT NULL,
            id_position INTEGER,
            FOREIGN KEY (id_position) REFERENCES positionEEG(id)
        );
    """)

    # --- Ajout des colonnes temps_debut et temps_fin requises par le module topomap ---
    conn.execute("""
        CREATE TABLE grapheTopomap (
            id INTEGER PRIMARY KEY DEFAULT nextval('seq_topomap_id'),
            nom_graphe VARCHAR NOT NULL,
            temps_debut DOUBLE,
            temps_fin DOUBLE
            
        );
    """)

    conn.execute("""
        CREATE TABLE grapheEnveloppe (
            id INTEGER PRIMARY KEY DEFAULT nextval('seq_enveloppe_id'),
            nom_graphe VARCHAR NOT NULL,
            id_position INTEGER,
            FOREIGN KEY (id_position) REFERENCES positionEEG(id)
        );
    """)

    conn.execute("""
        CREATE TABLE grapheAsymetrie (
            id INTEGER PRIMARY KEY DEFAULT nextval('seq_asymetrie_id'),
            nom_graphe VARCHAR NOT NULL,
            paire_positions VARCHAR NOT NULL
        );
    """)


    print("Base de données DuckDB initialisée avec succès.")
    return conn

def main(cfg : SessionConfig ) :


    conn = init_database(cfg)

    if not os.path.exists(cfg.xdf_file):
        print(f"Erreur : Fichier '{cfg.xdf_file}' introuvable.")
        return

    print(f"\n--- Chargement du fichier XDF : {cfg.xdf_file} ---")
    streams, header = pyxdf.load_xdf(cfg.xdf_file)

    eeg_stream = next((s for s in streams if s['info']['type'][0] == 'EEG'), None)
    if eeg_stream is None:
        raise RuntimeError("Aucun flux EEG trouvé.")

    marker_streams = [s for s in streams if s['info']['type'][0] == 'MarkerEEG']
    if marker_streams:
        m_stream = marker_streams[0]
        marker_times = np.array(m_stream['time_stamps'])
        marker_labels = [str(m[0]) for m in m_stream['time_series']]
    else:
        marker_times, marker_labels = np.array([]), []

    start_sample = 2500
    start_time = eeg_stream['time_stamps'][0]
    
    # Brute data shape: (n_samples, n_channels)
    eeg_data_raw = np.array(eeg_stream['time_series'])
    sfreq = int(float(eeg_stream['info']['nominal_srate'][0]))

    offset_time = start_sample / sfreq
    marker_times_rel = marker_times - start_time - offset_time

    try:
        channels = eeg_stream['info']['desc'][0]['channels'][0]['channel']
        channel_labels = [ch['label'][0] for ch in channels]
    except Exception:
        channel_labels = [f"EEG_{i+1}" for i in range(eeg_data_raw.shape[1])]

    n_channels = eeg_data_raw.shape[1]
    print(f"Traitement de {n_channels} canaux EEG...\n")

    # --- Préparation du filtrage global pour les topomaps (shape: n_channels, n_samples) ---
    eeg_data_filtered_all = eeg_data_raw[start_sample:].T
    eeg_data_filtered_all = bandpass_filter(eeg_data_filtered_all, sfreq)
    eeg_data_filtered_all = notch_filter(eeg_data_filtered_all, sfreq)



    # 1. Enregistrement dans nom_identifiant
    conn.execute("INSERT INTO identifiant (nom_identifiant) VALUES (?)", (cfg.name_session,))

    


    # Boucle canal par canal pour les métriques, FFT, SCA et Energy
    for chan_idx in range(n_channels):

        chan_label = channel_labels[chan_idx]
        
        if chan_label == 'NONE' : # pas de capteur présent ou désactivé
            continue

         

        raw_signal = eeg_data_raw[start_sample:, chan_idx]
        #signaux_par_canal[chan_label] = raw_signal

        # 1. Enregistrement dans positionEEG
        conn.execute("INSERT INTO positionEEG (nom_position) VALUES (?)", (chan_label,))
        id_position = conn.execute("SELECT MAX(id) FROM positionEEG").fetchone()[0]

        print(f"--> Canal #{id_position} : {chan_label}")

        # 2. Calcul et sauvegarde des métriques statistiques
        calculer_et_sauvegarder_resultats(conn, id_position, chan_label, raw_signal, sfreq)

        # 3. Traitement FFT
        traiter_et_sauvegarder_fft(conn, id_position, chan_label, raw_signal, sfreq, cfg)

        # 4. Traitement Scalogramme
        traiter_et_sauvegarder_sca(conn, id_position, chan_label, raw_signal, sfreq, marker_times_rel, marker_labels, cfg)

        # 5. Traitement Énergie Relative (Theta, Alpha, Beta)
        traiter_et_sauvegarder_energie(conn, id_position, chan_label, raw_signal, sfreq, marker_times_rel, marker_labels, cfg)

        # 6. Traitement Courbe EEG 
        traiter_et_sauvegarder_courbe_eeg(conn, id_position, chan_label, raw_signal, sfreq, marker_times_rel, marker_labels, cfg)



    
    # --- 7. Génération globale des Topomaps (HORS de la boucle des canaux) ---
    # On associe par défaut les topomaps au premier ID de position (ou un identifiant global de session)
    
    id_position_topo = 1 
    
    generer_et_sauvegarder_topomaps(
        db_conn=conn,
        eeg_data_filtered=eeg_data_filtered_all,
        sfreq=sfreq,
        channel_labels=channel_labels,
        marker_times_relative=marker_times_rel,
        marker_labels=marker_labels,
        cfg = cfg
    )
    
    

    # Génération de l'image de la tête
    
    generer_et_sauvegarder_tete(db_conn=conn, active_channels=channel_labels, cfg =cfg )


    

    # Affichage du bilan complet
    print("\n=== Résumé des données en BDD (DuckDB) ===")
    df_summary = conn.execute("""
        SELECT 
            p.id, p.nom_position, 
            f.nom_graphe AS fft, 
            s.nom_graphe AS sca, 
            e.nom_graphe AS energy,
            g.nom_graphe AS grapheEEG
        FROM positionEEG p
        LEFT JOIN grapheFFT f ON p.id = f.id_position
        LEFT JOIN grapheSCA s ON p.id = s.id_position
        LEFT JOIN energie e ON p.id = e.id_position
        LEFT JOIN grapheEEG g ON  p.id = g.id_position
    """).fetchdf()
    print(df_summary.to_string(index=False))

    conn.close()
    print("\nTous les traitements, y compris les topomaps glissantes, sont terminés avec succès !")
    

    generer_rapport_html(cfg =cfg , inclure_topomap = False)

    generer_rapport_html(cfg =cfg)

    



if __name__ == "__main__":

    XDF_FILE = "data/Conscious_EEG_20251003_163535187.xdf"
    SESSION_ID ="FGYHJ34567GFZAXCVFTH"

    cfg = init_environment_rapport (session_id = SESSION_ID)

    cfg.xdf_file =XDF_FILE
    main ( cfg = cfg)


