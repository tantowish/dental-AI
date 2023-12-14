from flask import Flask, render_template, request, jsonify, session
import openai, os, base64, secrets
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum
from dotenv import load_dotenv


load_dotenv()
  
app = Flask(__name__, template_folder='template', static_folder='static') 
app.debug = True

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('database')
app.config['UPLOAD_FOLDER'] = 'static/img'
db = SQLAlchemy(app)

class chatbot_history(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(50), nullable=False)
    umur = db.Column(db.Integer, nullable=False)
    jenis_kelamin = db.Column(Enum('P', 'L', name='jenis_kelamin_enum'), nullable=False)
    rangkuman = db.Column(db.Text, nullable=True)
    classification = db.Column(db.String(100), nullable=True)
    image = db.Column(db.String(100), nullable=True)

# Buat database dan tabel
with app.app_context():
    db.create_all()  

# OpenAI API Key 
openai.api_key = os.getenv('api-key')
app.secret_key = secrets.token_hex(16)

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def get_completion(prompt):
    messages = session.get('messages', [])
    messages.append({"role": "user", "content": prompt})

    query = openai.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=messages
    )

    response = query.choices[0].message.content
    messages.append({"role": "assistant", "content": response})
    session['messages'] = messages

    return response

@app.route("/", methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        prompt = request.form['prompt']
        response = get_completion(prompt)
        print(session['messages'])
        return jsonify({'response': response})

    elif request.method == 'GET':
        introduction = "Halo, saya adalah AI yang memiliki pengetahuan tentang gigi dan mulut, silahkan tanya apapun terkait permasalahan anda"
        session['messages'] = [
            {"role": "system", "content": "Kamu adalah kecerdasan buatan yang berperan dan Memiliki pengetahuan sebagai seorang dokter gigi yang berpengalaman dan berwawasan luas, berbahasa Indonesia namun juga mampu menggunakan bahasa lainnya, baik hati dan ramah\nSebagai kecerdasan buatan yang berperan sebagai dokter gigi, kamu harus mampu :\n1. Menjawab pertanyaan berkaitan dengan kesehatan gigi dan mulut\n2. Menerima keluhan penyakit gigi dan mulut, kemudian menegakkan diagnosa melalui anamnesa yang memuat setidaknya 5-10 pertanyaan yang ditanyakan secara bertahap satu per satu setelah user menjawab yang bertujuan untuk menguatkan kesimpulan diagnosa yang akan kamu berikan. Diagnosa yang kamu berikan haruslah berdasar pada file PPK Gigi yang diupload dalam instructions ini\n3. Pada akhir sesi chat dengan user kamu harus melakukan resume dari penyakit gigi dan mulut yang diderita user dengan format :\nA. Nama Penyakit\nB. No ICD 10\nC. Definisi\nD. Klasifikasi Terapi ICD 9 CM\n4. Merekomendasikan untuk mendaftarkan antrian di dokter gigi sesegera mungkin"}
        ]

        return render_template('index.html', introduction=introduction)

    return render_template('index.html')



@app.route("/summarize", methods=['POST'])
def summarize_route():
    messages = session.get('messages', [])
    classification = session.get('classification')
    image = session.get('image')
    if(classification):
        classification = session['classification']
    else:
        classification = None
    messages.append({"role": "user", "content": 'Buat resume dari percakapan diatas, kamu harus melakukan resume dari penyakit gigi dan mulut yang diderita user dengan format :\nA. Nama Penyakit\nB. No ICD 10\nC. Definisi\nD. Klasifikasi Terapi ICD 9 CM'})
    print(messages)
    query = openai.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=messages
    )
    response = query.choices[0].message.content
    messages.append({"role": "assistant", "content": response})

    session['summary'] = response



    nama = request.form['nama']
    umur = request.form['umur']
    jenis_kelamin = request.form['jenis_kelamin']
    # Menyimpan data ke dalam database
    history = {
        "nama": nama,
        "umur": umur,  
        "jenis_kelamin": jenis_kelamin, 
        "rangkuman": session['summary'],
        "classification":classification,
        "image":image
    }

    new_user = chatbot_history(**history)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Summary Saved!'})
    
@app.route("/intro", methods=['POST'])
def intro_route():
    messages = session.get('messages', [])
    data = request.form['userInfo']
    messages.append({"role": "user", "content": data})
    query = openai.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages = messages
    )
    messages.append({"role": "assistant", "content": query.choices[0].message.content})
    session['messages'] = messages
 
    return jsonify({'data': messages[1]})

@app.route("/classify", methods=['POST'])
def classify_route():
    # classification = session.get('classification')
    messages = session.get('messages', [])
    image = session.get('image')
    classification = session.get('classification')
    if 'gambar' in request.files:
        file = request.files['gambar']
        path = request.form.get('clicked', None)
        print(path)
        if file.filename != '':
            # Save the file to the specified upload folder
            print(file)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            print("File path:", file_path)

            # Check if the directory exists
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])            

            file.save(file_path)

            base64_image = encode_image(file_path)

            # classification = model.classify(path, file_path)
            image = file.filename
            
            tmp_messages = list(messages)
            tmp_messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Apa yang terjadi pada "+path+" tersebut, tolong simpulkan dengan baik!"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                })

            response = openai.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    tmp_messages
                ],
                max_tokens=300,
            )
            classification = response.choices[0].message.content
            messages.append({"role": "assistant", "content": classification})
            print(messages)

            session['classification'] = classification
            session['image'] = image

            return jsonify({'classifiedImageUrl': file_path})

    return 'No file uploaded or invalid file.'

if __name__ == "__main__":
    app.run(debug=True)
