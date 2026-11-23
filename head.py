import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os
from config import SessionConfig

#def generer_et_sauvegarder_tete(db_conn, active_channels  , temp_dir="tmp"):
def generer_et_sauvegarder_tete(db_conn, active_channels  , cfg: SessionConfig):
    """
    Génère la cartographie 2D de la tête EEG avec les électrodes actives en rouge
    et sauvegarde l'image à l'emplacement indiqué.
    """

    img_filename ="head.webp"
    head_img_path = os.path.join(cfg.temp_dir_img, img_filename)
        

    # Enregistrement dans DuckDB (table grapheHead)
    db_conn.execute("INSERT INTO grapheHead (img_head) VALUES ( ?)", ( img_filename, ) )

    

    # Coordonnées (x, y) pour les électrodes (Système 10-20 normalisé)
    positions_10_20 = {
        'Fp1': (-0.3, 0.8), 'Fp2': (0.3, 0.8),
        'F3':  (-0.5, 0.5), 'F4':  (0.5, 0.5),  'Fz':  (0.0, 0.5),
        'C3':  (-0.4, 0.0), 'C4':  (0.4, 0.0),  'Cz':  (0.0, 0.0),
        'T3':  (-0.9, 0.0), 'T4':  (0.9, 0.0),
        'P3':  (-0.5, -0.5), 'P4':  (0.5, -0.5), 'Pz':  (0.0, -0.5),
        'O1':  (-0.3, -0.8), 'O2':  (0.3, -0.8), 'Oz':  (0.0, -0.8)
    }

    fig, ax = plt.subplots(figsize=(4, 4), dpi=150)
    ax.set_aspect('equal')
    ax.axis('off')

    # Dessiner la tête (cercle principal)
    head_circle = plt.Circle((0, 0), 1.0, color='black', fill=False, linewidth=2.5)
    ax.add_patch(head_circle)

    # Dessiner le nez
    nose = plt.Polygon([[-0.1, 1.0], [0.1, 1.0], [0.0, 1.18]], color='black', fill=True)
    ax.add_patch(nose)

    # Dessiner les oreilles
    left_ear = patches.Ellipse((-1.05, 0.0), 0.1, 0.25, angle=0, color='black', fill=True)
    right_ear = patches.Ellipse((1.05, 0.0), 0.1, 0.25, angle=0, color='black', fill=True)
    ax.add_patch(left_ear)
    ax.add_patch(right_ear)

    # Dessiner les électrodes et leurs étiquettes
    for name, (x, y) in positions_10_20.items():
        face_color = 'red' if name in active_channels else 'white'
        circle = plt.Circle((x, y), 0.07, facecolor=face_color, edgecolor='black', linewidth=1.5, zorder=3)
        ax.add_patch(circle)
        
        if name == 'O1':
            ax.text(x - 0.12, y, name, fontsize=6, ha='right', va='center', color='black')
        elif name == 'O2':
            ax.text(x + 0.12, y, name, fontsize=6, ha='left', va='center', color='black')
        else:
            ax.text(x, y - 0.12, name, fontsize=6, ha='center', va='top', color='black')

    ax.set_xlim(-1.4, 1.4)
    ax.set_ylim(-1.4, 1.4)
    plt.title("Cartographie EEG - Positions Actives", fontsize=10,  pad=15)
    
    # Sauvegarde du fichier image


    fig.savefig(head_img_path, format="webp", pil_kwargs={"quality": 90}, bbox_inches='tight')
    plt.close(fig)

