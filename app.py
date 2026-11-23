import io
import os
import shutil
import zipfile
from pathlib import Path
from flask import Flask, jsonify, request, send_file
from main import init_environment_rapport, main

app = Flask(__name__)


@app.route("/", methods=["GET", "HEAD"])
def health():
    return "OK", 200


@app.route("/upload-xdf/<string:session_id>", methods=["POST"])
def receive_xdf(session_id):
    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier trouvé dans la requête (clé 'file' manquante)"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Nom de fichier vide"}), 400

    cfg = None
    try:
        filename = f"{session_id}.xdf"
        cfg = init_environment_rapport(session_id)
        upload_folder = cfg.temp_dir_data
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)

        cfg.xdf_file = filepath
        file.save(filepath)

        main(cfg)
        session_output_dir = cfg.temp_dir_img

        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(session_output_dir):
                for f in files:
                    if f.endswith(".xdf"):
                        continue
                    full_path = os.path.join(root, f)
                    arcname = os.path.relpath(full_path, session_output_dir)
                    zf.write(full_path, arcname=arcname)

        memory_file.seek(0)
        return send_file(
            memory_file,
            mimetype="application/zip",
            as_attachment=True,
            download_name=f"resultats_{session_id}.zip",
        )
        del memory_file
    except Exception as e:

        return jsonify({"error": f"Erreur lors du traitement : {e}"}), 500
    finally:
        if cfg is not None and getattr(cfg, "temp_session_id", None):
            rep_session = Path(cfg.temp_session_id)
            if rep_session.exists() and rep_session.is_dir():
                shutil.rmtree(rep_session, ignore_errors=True)

if __name__ == '__main__':
    # Lancement du serveur sur toutes les interfaces du conteneur, port 8021
    app.run(host='0.0.0.0', port=8021)       
