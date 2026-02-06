from flask import Flask, render_template_string, request, send_file
import yt_dlp
import os
import tempfile
import glob

app = Flask(__name__)

# --- INTERFACE HTML/CSS/JS ---
HTML_CODE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Converto</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f0f1a; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        
        .main-card { background: #1a1a2e; padding: 2.5rem; border-radius: 20px; text-align: center; width: 100%; max-width: 480px; box-shadow: 0 20px 50px rgba(0,0,0,0.6); border: 1px solid #30304b; }
        
        h1 { color: #ff0000; margin-bottom: 10px; font-size: 2.2rem; text-transform: uppercase; }
        p { color: #888; margin-bottom: 30px; }
        
        .input-group { display: flex; gap: 10px; margin-bottom: 20px; }
        input[type="text"] { flex: 1; padding: 15px; border-radius: 10px; border: 1px solid #30304b; background: #0f0f1a; color: white; outline: none; font-size: 1rem; }
        
        .btn-paste { background: #30304b; color: white; border: none; padding: 0 15px; border-radius: 10px; cursor: pointer; transition: 0.3s; font-size: 1.2rem; }
        .btn-paste:hover { background: #45456b; }

        select { width: 100%; padding: 15px; border-radius: 10px; border: 1px solid #30304b; background: #0f0f1a; color: white; margin-bottom: 20px; cursor: pointer; font-size: 1rem; }
        
        button#download-btn { width: 100%; padding: 15px; border-radius: 10px; border: none; background: #ff0000; color: white; font-weight: bold; font-size: 1.1rem; cursor: pointer; transition: 0.3s; }
        button#download-btn:hover { background: #cc0000; transform: translateY(-2px); }

        /* --- LOADER STYLE (UIVERSE) --- */
        #loader-overlay { display: none; margin-top: 30px; }
        .loader-wrapper { width: fit-content; gap: 10px; margin: auto; }
        .folder { width: min-content; margin: auto; animation: float 2s infinite linear; }
        .folder .top { background-color: #FF8F56; width: 60px; height: 12px; border-top-right-radius: 10px; }
        .folder .bottom { background-color: #FFCE63; width: 100px; height: 70px; box-shadow: 5px 5px 0 0 #0f0f1a; border-top-right-radius: 8px; }
        .loader-title { font-size: .95em; color: #FFCE63; text-align: center; margin-top: 15px; font-weight: bold; letter-spacing: 1px; }

        @keyframes float {
            0%, 100% { transform: translatey(0px); }
            50% { transform: translatey(-25px); }
        }
    </style>
</head>
<body>
    <div class="main-card">
        <h1>Converto</h1>
        <p>Convertisseur YouTube MP3 / WAV / MP4</p>
        
        <form action="/convert" method="post" id="convert-form">
            <div class="input-group">
                <input type="text" name="url" id="url-input" placeholder="Collez votre lien ici..." required>
                <button type="button" class="btn-paste" onclick="pasteLink()" title="Coller le lien">📋</button>
            </div>
            
            <select name="format">
                <option value="mp3">🎵 Format Audio MP3</option>
                <option value="wav">🎼 Format Audio WAV (HQ)</option>
                <option value="mp4">🎬 Format Vidéo MP4</option>
            </select>
            
            <button type="submit" id="download-btn">Convertir & Télécharger</button>
        </form>

        <div id="loader-overlay">
            <div class="loader-wrapper">
                <div class="folder">
                    <div class="top"></div>
                    <div class="bottom"></div>
                </div>
                <div class="loader-title">TRAITEMENT EN COURS...</div>
            </div>
        </div>
    </div>

    <script>
        // Bouton Coller
        async function pasteLink() {
            try {
                const text = await navigator.clipboard.readText();
                document.getElementById('url-input').value = text;
            } catch (err) {
                alert("Permission de lecture du presse-papier refusée.");
            }
        }

        // Affichage du loader
        document.getElementById('convert-form').onsubmit = function() {
            document.getElementById('download-btn').style.display = "none";
            document.getElementById('loader-overlay').style.display = "block";

            // Réinitialisation automatique après 15 secondes pour permettre un nouveau clic
            setTimeout(() => {
                document.getElementById('download-btn').style.display = "block";
                document.getElementById('loader-overlay').style.display = "none";
            }, 15000);
        };
    </script>
</body>
</html>
"""

# --- LOGIQUE BACKEND ---
@app.route('/')
def index():
    return render_template_string(HTML_CODE)

@app.route('/convert', methods=['POST'])
def convert():
    video_url = request.form.get('url')
    file_format = request.form.get('format')
    download_path = tempfile.gettempdir()
    
    # Détection dynamique du dossier ffmpeg local (ex: ffmpeg-8.0.1...)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ffmpeg_folders = glob.glob(os.path.join(current_dir, "ffmpeg*"))
    
    # On définit le chemin seulement si le dossier existe localement
    ffmpeg_bin = os.path.join(ffmpeg_folders[0], "bin") if ffmpeg_folders else None

    ydl_opts = {
        'format': 'bestaudio/best' if file_format in ['mp3', 'wav'] else 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
        'noplaylist': True,
        'ffmpeg_location': ffmpeg_bin,
    }

    if file_format in ['mp3', 'wav']:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': file_format,
            'preferredquality': '192',
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            temp_filename = ydl.prepare_filename(info)
            
            if file_format in ['mp3', 'wav']:
                base, _ = os.path.splitext(temp_filename)
                final_filename = base + f".{file_format}"
            else:
                final_filename = temp_filename

            return send_file(final_filename, as_attachment=True)
    except Exception as e:
        return f"<h1>Erreur</h1><p>{str(e)}</p><a href='/'>Retour</a>"

if __name__ == '__main__':
    app.run(debug=True, port=5000)