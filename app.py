from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Beyin 101 Video Generator</title>
        <style>
            body { font-family: Arial; padding: 50px; }
            h1 { color: #333; }
            select { padding: 10px; font-size: 16px; }
            button { padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer; font-size: 16px; }
            button:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <h1>🧠 Beyin 101 Video Generator</h1>
        <p>Konu seçin:</p>
        <select id="topic">
            <option value="">-- Seç --</option>
            <option value="hafiza">Hafıza Nasıl Çalışır?</option>
            <option value="dopamin">Dopamin: Motivasyonun Kimyası</option>
            <option value="uyku">REM Uykusu ve Rüyalar</option>
            <option value="anksiyete">Kaygı Beyni Nasıl Etkiler?</option>
            <option value="dikkat">Dikkat ve Konsantrasyon</option>
        </select>
        <br><br>
        <button onclick="generate()">OLUŞTUR</button>
        <div id="status"></div>
        
        <script>
            function generate() {
                const topic = document.getElementById('topic').value;
                if (!topic) {
                    document.getElementById('status').innerHTML = '<p style="color: red;">Lütfen konu seçiniz!</p>';
                    return;
                }
                document.getElementById('status').innerHTML = '<p style="color: blue;">Video oluşturuluyor... (2-3 dakika)</p>';
            }
        </script>
    </body>
    </html>
    '''

@app.route('/api/generate', methods=['POST'])
def generate():
    return {'status': 'success', 'message': 'Video oluşturuluyor...'}

if __name__ == '__main__':
    app.run(debug=True)
