from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Beyin 101</title></head>
    <body>
        <h1>Beyin 101 Video Generator</h1>
        <select id="topic">
            <option value="hafiza">Hafıza</option>
            <option value="dopamin">Dopamin</option>
            <option value="uyku">REM Uykusu</option>
            <option value="anksiyete">Kaygı</option>
            <option value="dikkat">Dikkat</option>
        </select>
        <button onclick="alert('Video oluşturuluyor...')">OLUŞTUR</button>
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run()
