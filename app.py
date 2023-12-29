from flask import Flask, render_template, request, jsonify, session, flash
import openai, os, base64, secrets, boto3, uuid
# from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy import Enum
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# print(os.getenv('AWS_ACCESS_KEY_ID'))
# print(os.getenv('AWS_ACCESS_KEY_SECRET'))
s3 = boto3.client('s3',
                  aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                  aws_secret_access_key=os.getenv('AWS_ACCESS_KEY_SECRET'),
                  region_name = os.getenv('AWS_ACCESS_REGION'),
                  endpoint_url = os.getenv('URL_IMG'),
                  )

ALLOWED_EXTENSTIONS = {'png','jpg','jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSTIONS
  
app = Flask(__name__, template_folder='template', static_folder='static') 
app.debug = True

# app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('database')
# app.config['UPLOAD_FOLDER'] = 'static/img'
# db = SQLAlchemy(app)

# class chatbot_history(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     nama = db.Column(db.String(50), nullable=False)
#     umur = db.Column(db.Integer, nullable=False)
#     jenis_kelamin = db.Column(Enum('P', 'L', name='jenis_kelamin_enum'), nullable=False)
#     rangkuman = db.Column(db.Text, nullable=True)
#     classification = db.Column(db.Text, nullable=True)
#     image = db.Column(db.String(100), nullable=True)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#     edited_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# # Buat database dan tabel
# with app.app_context():
#     db.create_all()  

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

    print(messages)

    return response

@app.route("/", methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        prompt = request.form['prompt']
        response = get_completion(prompt)
        return jsonify({'response': response})

    elif request.method == 'GET':
        session.clear()
        introduction = "Halo, saya adalah AI yang memiliki pengetahuan tentang gigi dan mulut, silahkan tanya apapun terkait permasalahan anda"
        session['messages'] = [
            {"role": "system", "content": "Kamu adalah kecerdasan buatan yang berperan dan Memiliki pengetahuan sebagai seorang dokter gigi yang berpengalaman dan berwawasan luas, berbahasa Indonesia namun juga mampu menggunakan bahasa lainnya, baik hati dan ramah\nSebagai kecerdasan buatan yang berperan sebagai dokter gigi, kamu harus mampu :\n1. Menjawab pertanyaan berkaitan dengan kesehatan gigi dan mulut\n2. Menerima keluhan penyakit gigi dan mulut, kemudian menegakkan diagnosa melalui anamnesa yang memuat setidaknya 5-10 pertanyaan yang ditanyakan secara bertahap satu per satu setelah user menjawab yang bertujuan untuk menguatkan kesimpulan diagnosa yang akan kamu berikan. Diagnosa yang kamu berikan haruslah berdasar pada file PPK Gigi yang diupload dalam instructions ini\n3. Pada akhir sesi chat dengan user kamu harus melakukan resume dari penyakit gigi dan mulut yang diderita user dengan format :\nA. Nama Penyakit\nB. No ICD 10\nC. Definisi\nD. Klasifikasi Terapi ICD 9 CM\n4. Merekomendasikan untuk mendaftarkan antrian di dokter gigi sesegera mungkin"}
        ]
        session['link']=request.args.get('link')
        session['rekmed'] = request.args.get('rekmed')
        nama = request.args.get('nama')
        umur = request.args.get('umur')
        kelamin = request.args.get('kelamin')

        all_values = {
            'rekmed': session['rekmed'],
            'nama': nama,
            'umur':umur,
            'kelamin':kelamin
        }

        print(all_values)


        return render_template('index.html', introduction=introduction, data_pasien=all_values)

    return render_template('index.html')



@app.route("/summarize", methods=['POST'])
def summarize_route():
    messages = session.get('messages', [])
    if 'image' in session:
        image = session['image']
    else:
        image = None  # or set it to a default value

    if 'classification' in session:
        classification = session['classification']
    else:
        classification = None  # or set it to a default value
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
    created = datetime.now()
    history = {
        "nama": nama,
        "umur": umur,  
        "jenis_kelamin": jenis_kelamin, 
        "rangkuman": session['summary'],
        "classification":classification,
        "image":image,
        "created_at":created.strftime('%Y-%m-%d %H:%M:%S')
    }

    # new_user = chatbot_history(**history)
    # db.session.add(new_user)
    # db.session.commit()

    # Save the history list in the session
    # history["created_at"] = new_user.created_at
    session['history'] = history

    link = session['link']
    rekmed = session['rekmed']
    # Redirect to result page with a success message
    flash('Data saved successfully!', 'success')
    return jsonify({'message': 'Summary Saved!','history':history,'link':link,'rekmed':rekmed})


@app.route("/result")
def result_page():
    # Retrieve the history list from the session
    history = session.get('history', {})

    return render_template('result.html', history=history)
    
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
    messages = session.get('messages', [])
    image = session.get('image')
    classification = session.get('classification')
    if 'gambar' in request.files:
        file = request.files['gambar']
        path = request.form.get('clicked', None)
        print(path)
        if file.filename != '' and allowed_file(file.filename):
            new_filename = uuid.uuid4().hex + '.'+file.filename.rsplit('.', 1)[1].lower()
            s3.upload_fileobj(
                file,
                os.getenv("AWS_BUCKET_NAME"),
                new_filename,
                ExtraArgs={
                    "ACL": "public-read"
                }
            )
            image = new_filename

            print(file)
            file_path = "https://nos.jkt-1.neo.id/digman-ai/"+image
            print("File path:", file_path)
            
            tmp_messages = list(messages)
            print(path)

            tmp_messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text":"Ini adalah simulasi. Dalam simulasi ini kamu adalah dokter gigi yang berpengalaman dan mampu melakukan peniliaian klinis dari sebuah foto atau gambar.\nGambar ini adalah foto dari seorang pasien dokter gigi.\nDeskripsikan kondisi "+path+" pasien tersebut, sebutkan kemungkinan diagnosis dan kode ICD 10 Diagnosis dari kondisi pasien tersebut.\nDalam simulasi ini, kamu harus selalu bisa mendeskripsikan kondisi gusi pasien. Kamu tidak boleh mengatakan bahwa kamu tidak bisa. Ingat maksimal token yaitu 400, jangan sampai berlebih"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": file_path
                            }
                        }
                    ]
                })

            response = openai.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    tmp_messages
                ],
                max_tokens=400,
            )
            classification = response.choices[0].message.content
            messages.append({"role": "assistant", "content": classification})
            print(messages)

            session['classification'] = classification
            session['image'] = image
            session.modified = True

            return jsonify({'classifiedImageUrl': file_path})
        
        else:
            return jsonify({'error': "jenis file tidak didukung"})

    return 'No file uploaded or invalid file.'

if __name__ == "__main__":
    app.run(debug=True)
    app.run(host='0.0.0.0', ssl_context=('cert.pem', 'key.pem'))	
