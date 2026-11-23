import os
import io
import zipfile
from flask import Flask, request, jsonify, send_file
from pathlib import Path
from main import main , init_environment_rapport
from config import SessionConfig
import shutil

app = Flask(__name__)



@app.route('/upload-xdf/<string:session_id>', methods=['POST'])
def receive_xdf(session_id):


    try :
        """
        Reçoit un fichier XDF depuis le poste client avec un ID unique dans l'URL.
        Exemple d'URL appelée par le client : http://<ip-serveur>:5000/upload-xdf/abc123xyz
        """
        # 1. Vérification de la présence du fichier dans la requête multipart/form-data
        if 'file' not in request.files:
            return jsonify({"error": "Aucun fichier trouvé dans la requête (clé 'file' manquante)"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "Nom de fichier vide"}), 400

        # 2. Sécurisation et enregistrement du fichier avec l'identifiant unique
        filename = f"{session_id}.xdf"
        cfg = init_environment_rapport(session_id )
        # Dossier où seront stockés les fichiers XDF reçus
        UPLOAD_FOLDER = cfg.temp_dir_data
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        cfg.xdf_file =filepath
        file.save(filepath)

        print(f" [RECEPTION] Fichier XDF bien reçu pour la session ID : {session_id}")
        print(f"            Enregistré sous : {filepath}")

        # TODO : C'est ici que vous appellerez votre pipeline principal (ex: lancer_pipeline(filepath, session_id))
        main (cfg)
        session_output_dir = cfg.temp_dir_img
        # 2. Création d'une archive ZIP en mémoire (RAM) contenant tous les fichiers du dossier de session
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(session_output_dir):
                for f in files:
                    full_path = os.path.join (root, f )
                    # On exclut le fichier XDF d'origine si on ne veut renvoyer que les résultats, ou on le garde
                    if f.endswith('.xdf'):
                        continue
                    arcname = os.path.relpath(full_path , session_output_dir)
                    # Ajout du fichier dans le zip avec un chemin relatif propre
                    zf.write(full_path, arcname=arcname)
        
        memory_file.seek(0)
    finally:
        rep_session = Path(cfg.temp_session_id)   
            
        if rep_session.exists() and rep_session.is_dir():
            shutil.rmtree(rep_session)

    # 3. Envoi du fichier ZIP directement en réponse HTTP
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f"resultats_{session_id}.zip"
    )





    return jsonify({
        "status": "success",
        "message": f"Fichier XDF reçu avec succès pour l'identifiant {session_id}",
        "session_id": session_id,
        "saved_path": filepath
    }), 200

if __name__ == '__main__':
    # Lancement du serveur sur toutes les interfaces du conteneur, port 5000
    app.run(host='0.0.0.0', port=8021)
