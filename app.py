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
    <title>Converto</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f0f1a; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        
        /* Conteneur Principal */
        .main-card { background: #1a1a2e; padding: 2.5rem; border-radius: 20px; text-align: center; width: 480px; box-shadow: 0 20px 50px rgba(0,0,0,0.6); border: 1px solid #30304b; position: relative; }
        
        h1 { color: #ff0000; margin-bottom: 10px; font-size: 2rem; letter-spacing: 1px; }
        p { color: #888; margin-bottom: 30px; }
        
        .input-group { display: flex; gap: 10px; margin-bottom: 20px; }
        input[type="text"] { flex: 1; padding: 15px; border-radius: 10px; border: 1px solid #30304b; background: #0f0f1a; color: white; outline: none; }
        
        .btn-paste { background: #30304b; color: white; border: none; padding: 0 15px; border-radius: 10px; cursor: pointer; transition: 0.3s; font-size: 1.2rem; }
        .btn-paste:hover { background: #45456b; }

        select { width: 100%; padding: 15px; border-radius: 10px; border: 1px solid #30304b; background: #0f0f1a; color: white; margin-bottom: 20px; cursor: pointer; }
        
        button#download-btn { width: 100%; padding: 15px; border-radius: 10px; border: none; background: #ff0000; color: white; font-weight: bold; font-size: 1.1rem; cursor: pointer; transition: 0.3s; }
        button#download-btn:hover { background: #cc0000; transform: translateY(-2px); }

        /* --- STYLE DU LOADER (UIVERSE) --- */
        #loader-overlay { display: none; margin-top: 30px; }
        
        .loader-wrapper { width: fit-content; gap: 10px; margin: auto; }

        .folder { width: min-content; margin: auto; animation: float 2s infinite linear; }

        .folder .top { background-color: #FF8F56; width: 60px; height: 12px; border-top-right-radius: 10px; }

        .folder .bottom { background-color: #FFCE63; width: 100px; height: 70px; box-shadow: 5px 5px 0 0 #283149; border-top-right-radius: 8px; }

        .loader-wrapper .loader-title { font-size: .9em; color: #FFCE63; text-align: center; margin-top: 15px; font-weight: bold; }

        @keyframes float {
            0% { transform: translatey(0px); }
            50% { transform: translatey(-25px); }
            100% { transform: translatey(0px); }
        }
    </style>
</head>
<body>
    <div class="main-card">
        <h1>Converto</h1>
        <p>Prêt à télécharger vos fichiers ?</p>
        
        <form action="/convert" method="post" id="convert-form">
            <div class="input-group">
                <input type="text" name="url" id="url-input" placeholder="Collez le lien YouTube ici..." required>
                <button type="button" class="btn-paste" onclick="pasteLink()">📋</button>
            </div>
            
            <select name="format">
                <option value="mp3">🎵 Musique MP3</option>
                <option value="wav">🎼 Audio WAV (HQ)</option>
                <option value="mp4">🎬 Vidéo MP4</option>
            </select>
            
            <button type="submit" id="download-btn">Lancer la conversion</button>
        </form>

        <div id="loader-overlay">
            <div class="loader-wrapper">
                <div class="folder">
                    <div class="top"></div>
                    <div class="bottom"></div>
                </div>
                <div class="loader-title">Préparation des fichiers...</div>
            </div>
        </div>
    </div>

    <script>
        // Fonction pour coller le lien
        async function pasteLink() {
            try {
                const text = await navigator.clipboard.readText();
                document.getElementById('url-input').value = text;
            } catch (err) {
                console.log("Erreur de collage");
            }
        }

        // Gestion de l'affichage du loader au clic
        document.getElementById('convert-form').onsubmit = function() {
            const btn = document.getElementById('download-btn');
            const loader = document.getElementById('loader-overlay');

            // On cache le bouton et on montre le dossier flottant
            btn.style.display = "none";
            loader.style.display = "block";

            // On remet le bouton après 10 secondes pour pouvoir recommencer
            setTimeout(() => {
                btn.style.display = "block";
                loader.style.display = "none";
            }, 10000);
        };
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_CODE)

@app.route('/convert', methods=['POST'])
def convert():
    video_url = request.form.get('url')
    file_format = request.form.get('format')
    download_path = tempfile.gettempdir()
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ffmpeg_folders = glob.glob(os.path.join(current_dir, "ffmpeg*"))
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
        return f"Erreur : {str(e)}"

if __name__ == '__main__':
    app.run(debug=True, port=5000)