import json
import pymongo
from bson.objectid import ObjectId
import os

import pickle
import random
import string
import sys
import numpy as np
from util import base64_to_pil

from flask import Flask, redirect, url_for, request, render_template, Response, jsonify, session
from werkzeug.utils import secure_filename

#------------------------------------LIBRARY TENSORFLOW------------------------------------#

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.applications.imagenet_utils import preprocess_input, decode_predictions
from tensorflow.keras.applications.resnet50 import preprocess_input
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from tensorflow.keras.utils import get_file

from PIL import Image

import bleach
import io
import base64
from datetime import datetime

#------------------------------------LIBRARY CHATBOT------------------------------------#

from functools import wraps
from http.client import responses
from time import time
import time
from werkzeug.security import generate_password_hash, check_password_hash
from flask_restful import Resource, Api
from flask_httpauth import HTTPTokenAuth
from flask_cors import CORS
from datetime import timedelta



#------------------------------------APP------------------------------------#

app = Flask(__name__)
api = Api(app)

app.config['UPLOAD_TANAMAN'] = 'static/img/list/'
app.config['UPLOAD_FITUR'] = 'static/img/feature/'
app.config['UPLOAD_ARTIKEL'] = 'static/img/artikel/'
app.config['PERMANENT_SESSION_LIFETIME'] =  timedelta(minutes=120)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_DIR = 'static/img/riwayat/'


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
app.secret_key = 'MySecret'



#------------------------------------DATABASE------------------------------------#
try:
    mongo = pymongo.MongoClient(
        host="localhost",
        port=27017,
        serverSelectionTimeoutMS=1000
    )
    db = mongo.herbalia
    mongo.server_info()
except:
    print("ERROR Connect To Database")





#------------------------------------UPLOAD------------------------------------#

target_names = [
    'Daun Jambu Biji', 'Daun Kari', 'Daun Kemangi', 'Daun Kunyit',
    'Daun Mint', 'Daun Pepaya', 'Daun Sirih', 'Daun Sirsak',
    'Lidah Buaya', 'Teh Hijau'
]



model = load_model('modelnlp/model.h5')

def preprocess_image(image):
    img = image.resize((224, 224))
    img = np.array(img) / 255.0
    img = np.expand_dims(img, axis=0)
    return img

def classify_image(image):
    img = preprocess_image(image)
    preds = model.predict(img)
    predicted_class = np.argmax(preds)
    class_name = target_names[predicted_class]
    accuracy = round(preds[0][predicted_class] * 100) 
    return {
        'predicted_label': class_name,
        'predict_accuracy': accuracy
    }

@app.route('/scan', methods=['POST'])
def scan():
    try:
        image_data = request.json['image']
        image_data = image_data.split(",")[1] 
        image = Image.open(io.BytesIO(base64.b64decode(image_data)))
        image = image.convert('RGB')

        khasiat_id = None
        khasiat_list = []

        result = classify_image(image)

        tanaman_herbal = db.tanamanHerbal.find_one({'nama': result['predicted_label']})

        if tanaman_herbal and result['predict_accuracy'] > 70:
            nama_tanaman = tanaman_herbal['nama']
            nama_ilmiah = tanaman_herbal['namailmiah']
            deskripsi = tanaman_herbal['deskripsi']
            khasiat_id = tanaman_herbal['khasiat']
            referensi_id = tanaman_herbal['referensi']

            khasiat = db.khasiat.find_one({'_id': khasiat_id})
            if khasiat:
                khasiat_list = khasiat['khasiat']

            referensi = db.referensi.find_one({'_id': referensi_id})
            if referensi:
                referensi_list = referensi['referensi']

        image_filename = f"hasil_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        image_path = os.path.join(UPLOAD_DIR, image_filename)
        image.save(image_path)

        collection = db['riwayat']
        now = datetime.now()
        formatted_date = now.strftime("%Y-%m-%d")
        result_data = {
            "tanggal": formatted_date,
            'path': image_path,
            "hasil": result["predicted_label"],
            "akurasi": result["predict_accuracy"]
        }
        collection.insert_one(result_data)

        response_data = {
            'nama': nama_tanaman,
            'namailmiah': nama_ilmiah,
            'deskripsi': deskripsi,
            'khasiat': khasiat_list,
            'referensi': referensi_list,
            'akurasi': result["predict_accuracy"]
        }
        return jsonify(response_data)
    except Exception as e:
        print(str(e))
        return jsonify(error='Error processing image'), 400

@app.route('/upload', methods=['GET'])
def upload():
    return render_template('upload.html')





#------------------------------------SARAN------------------------------------#

@app.route('/saran', methods=['GET'])
def saran():
    return render_template('upload/saran.html')

@app.route('/tambahSaran', methods=['POST'])
def tambah_saran():
    saran_nama = request.form['saranNama']
    saran_deskripsi = request.form['saranDeskripsi']
    saran_gambar = request.files['saranGambar']

    saran_gambar.save('static/img/saran/{}'.format(saran_gambar.filename))

    now = datetime.now()
    formatted_date = now.strftime("%d-%m-%Y")
    saran = {
        'nama': saran_nama,
        'deskripsi': saran_deskripsi,
        'gambar': saran_gambar.filename,
        'tanggal': formatted_date
    }
    db.saran.insert_one(saran)

    return {
        'status': 'success',
        'message': 'Saran berhasil ditambahkan'
    }


#------------------------------------LANDING PAGE------------------------------------#

@app.route('/', methods=['GET'])
def index():
    dataFitur = db['landingpage_feature'].find({})
    dataTanaman = db['tanamanHerbal'].find({}).limit(8)
    dataArtikel = db['artikel'].find({})
    faqData = db['faq'].find({})
    return render_template('index.html',fitur  = dataFitur, tanaman = dataTanaman, artikel = dataArtikel, faqData = faqData)

@app.route('/chat', methods=['GET'])
def chat():
    return render_template('chat.html')


#------------------------------------DAFTAR TANAMAN------------------------------------#

@app.route('/daftarTanaman', methods=['GET'])
def daftarTanaman():
    query = request.args.get('query')

    if query:
        dataTanaman = db['tanamanHerbal'].find({'nama': {'$regex': query, '$options': 'i'}})
    else:
        dataTanaman = db['tanamanHerbal'].find({})
    return render_template('daftarTanaman.html', dataTanaman = dataTanaman)

@app.route('/daftarTanaman/search')
def cariTanaman():
    query = request.args.get('query')

    if query:
        dataTanaman = db['tanamanHerbal'].find({'nama': {'$regex': query, '$options': 'i'}})
    else:
        dataTanaman = db['tanamanHerbal'].find()

    return render_template('daftarTanaman.html', dataTanaman=dataTanaman )

@app.route('/daftarTanaman/<daftarTanaman_id>')
def detailTanaman(daftarTanaman_id):
    detailTanaman = db['tanamanHerbal'].find_one({'_id': ObjectId(daftarTanaman_id)})
    dataTanaman = db['tanamanHerbal'].find()

    khasiat_list = []
    referensi_list = []

    khasiat_id = detailTanaman.get("khasiat")
    referensi_id = detailTanaman.get("referensi")

    if khasiat_id:
        khasiat = db["khasiat"].find_one({"_id": khasiat_id})
        if khasiat:
            khasiat_list = khasiat["khasiat"]

    if referensi_id:
        referensi = db["referensi"].find_one({"_id": referensi_id})
        if referensi:
            referensi_list = referensi["referensi"]

    if detailTanaman:
        return render_template('detailTanaman.html', detailTanaman=detailTanaman, tanaman=dataTanaman, khasiatList=khasiat_list, referensiList=referensi_list)
    else:
        return 'Tanaman tidak ditemukan'





#------------------------------------ARTIKEL------------------------------------#

@app.route('/daftarArtikel')
def daftarArtikel():
    artikel = db['artikel'].find()
    return render_template('artikel/daftarArtikel.html', artikel=artikel)

@app.route('/daftarArtikel/<artikel_id>')
def detailArtikel(artikel_id):
    artikel = db['artikel'].find_one({'_id': ObjectId(artikel_id)})
    daftarArtikel = db['artikel'].find()
    if artikel:
        return render_template('artikel/detailArtikel.html', artikel=artikel, daftarArtikel=daftarArtikel)
    else:
        return 'Artikel tidak ditemukan'

# @app.route('/artikelLain', methods=['GET'])
# def artikelLain():
#     daftarArtikel = db['artikel'].find({})
#     return render_template('artikel/artikelLain.html', daftarArtikel=daftarArtikel)

@app.route('/daftarArtikel/search')
def cariArtikel():
    query = request.args.get('query')

    if query:
        artikel = db['artikel'].find({'judul': {'$regex': query, '$options': 'i'}})
    else:
        artikel = db['artikel'].find()

    return render_template('artikel/daftarArtikel.html', artikel=artikel )




#------------------------------------CHATBOT------------------------------------#







#------------------------------------ADMIN------------------------------------#

#------------------------------------LOGIN------------------------------------#

@app.route('/login', methods=['GET', 'POST'])
def login():
    session.permanent = True
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = db.admin.find_one({'username': username, 'password': password})
        if admin:
            session['username'] = admin['username']
            return redirect('/admin')
        else:
            return render_template('admin/login/login.html', error=True)
    return render_template('admin/login/login.html', error=False)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/admin')


APP_ROOT = os.path.dirname(os.path.abspath(__file__))

@app.route('/admin', methods=['GET'])
def admin():
    if 'username' in session:
        return render_template('admin/admin.html', username=session['username'])
    else:
        return redirect('/login')

#------------------------------------ADMIN PROFIL------------------------------------#

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

@app.route('/profil', methods=['GET'])
def profil():
    if 'username' in session:
        profils = db['profil'].find({})
        return render_template('admin/profil/profil.html', profils=profils)
    else:
        return redirect('/login')

@app.route('/editProfil/<id>', methods=['GET', 'POST'])
def editProfil(id):
    data = db.profil.find_one({'_id': ObjectId(id)})
    if not data:
        return 'Data tidak ditemukan'

    if request.method == 'POST':
        profilBaru = request.form['profil']
        db.profil.update_one(
            {'_id': ObjectId(id)},
            {'$set': {'profil': profilBaru}}
        )
        return redirect('/profil?success=true')

    return render_template('admin/profil/editProfil.html', profil=data)

#------------------------------------ADMIN TANAMAN------------------------------------#

@app.route('/adminTanaman')
def adminTanaman():
    if 'username' in session:
        tanaman = db['tanamanHerbal'].find({})
        return render_template("admin/daftarTanaman/adminTanaman.html",tanaman  = tanaman)
    else:
        return redirect('/login')

@app.route('/adminTanaman/editDeskripsi/<tanaman_id>', methods=['GET', 'POST'])
def editDeskripsi(tanaman_id):
    data = db.tanamanHerbal.find_one({'_id': ObjectId(tanaman_id)})
    if not data:
        return 'Data tidak ditemukan'

    if request.method == 'POST':
        deskripsiBaru = request.form['deskripsi']
        db.tanamanHerbal.update_one(
            {'_id': ObjectId(tanaman_id)},
            {'$set': {'deskripsi': deskripsiBaru}}
        )
        return redirect(url_for('editDeskripsi', tanaman_id=tanaman_id))

    return render_template("admin/daftarTanaman/edit/editDeskripsi.html", editTanaman=data)


@app.route('/adminTanaman/editKhasiat/<tanaman_id>', methods=['GET', 'POST'])
def edit_khasiat(tanaman_id):
    detailTanaman = db['tanamanHerbal'].find_one({'_id': ObjectId(tanaman_id)})
    dataTanaman = db['tanamanHerbal'].find()

    khasiat_list = []

    khasiat_id = detailTanaman.get("khasiat")

    if khasiat_id:
        khasiat = db["khasiat"].find_one({"_id": khasiat_id})
        if khasiat:
            khasiat_list = khasiat["khasiat"]

    if request.method == 'POST':
        khasiat = request.form.getlist('khasiat[]')

        db["khasiat"].update_one(
            {"_id": khasiat_id},
            {"$pull": {"khasiat": {"$nin": khasiat}}}
        )

        db["khasiat"].update_one(
            {"_id": khasiat_id},
            {"$addToSet": {"khasiat": {"$each": khasiat}}}
        )


        return redirect(url_for('edit_khasiat', tanaman_id=tanaman_id))

    return render_template('admin/daftarTanaman/edit/editKhasiat.html', detailTanaman=detailTanaman, tanaman=dataTanaman, khasiatList=khasiat_list)

@app.route('/adminTanaman/editReferensi/<tanaman_id>', methods=['GET', 'POST'])
def edit_referensi(tanaman_id):
    detailTanaman = db['tanamanHerbal'].find_one({'_id': ObjectId(tanaman_id)})
    dataTanaman = db['tanamanHerbal'].find()

    referensi_list = []

    referensi_id = detailTanaman.get("referensi")

    if referensi_id:
        referensi = db["referensi"].find_one({"_id": referensi_id})
        if referensi:
            referensi_list = referensi["referensi"]

    if request.method == 'POST':
        referensi = request.form.getlist('referensi[]')

        db["referensi"].update_one(
            {"_id": referensi_id},
            {"$pull": {"referensi": {"$nin": referensi}}}
        )

        db["referensi"].update_one(
            {"_id": referensi_id},
            {"$addToSet": {"referensi": {"$each": referensi}}}
        )


        return redirect(url_for('edit_referensi', tanaman_id=tanaman_id))

    return render_template('admin/daftarTanaman/edit/editReferensi.html', detailTanaman=detailTanaman, tanaman=dataTanaman, referensiList=referensi_list)

@app.route('/adminTanaman/search')
def cariAdminTanaman():
    query = request.args.get('query')

    if query:
        tanaman = db['tanamanHerbal'].find({'nama': {'$regex': query, '$options': 'i'}})
    else:
        tanaman = db['tanamanHerbal'].find()

    return render_template('admin/daftarTanaman/adminTanaman.html', tanaman=tanaman )

@app.route('/adminTanaman/<daftarTanaman_id>')
def detailAdminTanaman(daftarTanaman_id):
    detailTanaman = db['tanamanHerbal'].find_one({'_id': ObjectId(daftarTanaman_id)})
    dataTanaman = db['tanamanHerbal'].find()

    khasiat_list = []
    referensi_list = []

    khasiat_id = detailTanaman.get("khasiat")
    referensi_id = detailTanaman.get("referensi")

    if khasiat_id:
        khasiat = db["khasiat"].find_one({"_id": khasiat_id})
        if khasiat:
            khasiat_list = khasiat["khasiat"]

    if referensi_id:
        referensi = db["referensi"].find_one({"_id": referensi_id})
        if referensi:
            referensi_list = referensi["referensi"]
    
    if detailTanaman:
        return render_template('admin/daftarTanaman/adminDetailTanaman.html', detailTanaman=detailTanaman, tanaman=dataTanaman, khasiatList=khasiat_list, referensiList=referensi_list)
    else:
        return 'Tanaman tidak ditemukan'

@app.route('/tambah_tanaman', methods=['GET', 'POST'])
def tambah_tanaman():
    if 'username' in session:
        if request.method == 'POST':
            nama = request.form['nama']
            nama_ilmiah = request.form['nama_ilmiah']
            deskripsi = request.form['deskripsi']
            khasiat = request.form.getlist('khasiat[]')
            referensi = request.form.getlist('referensi[]')
            file = request.files['gambar']

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_TANAMAN'], filename))

            khasiat_data = {
                'tanaman_id': None,
                'khasiat': khasiat
            }
            referensi_data = {
                'tanaman_id': None,
                'referensi': referensi
            }
            khasiat_id = db['khasiat'].insert_one(khasiat_data).inserted_id
            referensi_id = db['referensi'].insert_one(referensi_data).inserted_id

            tanaman_herbal = {
                'path': filename,
                'nama': nama,
                'namailmiah': nama_ilmiah,
                'deskripsi': deskripsi,
                'khasiat': khasiat_id,
                'referensi': referensi_id
            }
            tanaman_id = db['tanamanHerbal'].insert_one(tanaman_herbal).inserted_id

            db['khasiat'].update_one(
                {'_id': khasiat_id},
                {'$set': {'tanaman_id': tanaman_id}}
            )

            db['referensi'].update_one(
                {'_id': referensi_id},
                {'$set': {'tanaman_id': tanaman_id}}
            )

            return render_template('admin/daftarTanaman/adminTanaman.html')

        return render_template('admin/daftarTanaman/tambahTanaman.html')
    else:
        return redirect('/login')

@app.route('/hapus_tanaman/<tanaman_id>', methods=['POST'])
def hapus_tanaman(tanaman_id):
    
    db['tanamanHerbal'].delete_one({'_id': ObjectId(tanaman_id)})
    db['khasiat'].delete_one({'tanaman_id': ObjectId(tanaman_id)})
    db['referensi'].delete_one({'tanaman_id': ObjectId(tanaman_id)})
    
    return redirect('/adminTanaman')



#------------------------------------ADMIN SARAN------------------------------------#

@app.route('/adminSaran')
def adminSaran():
    if 'username' in session:
        adminSaran = db['saran'].find({})
        return render_template("admin/saran/saran.html",adminSaran  = adminSaran)
    else:
        return redirect('/login')

@app.route('/adminSaran/<saran_id>')
def detailSaran(saran_id):
    saran = db['saran'].find_one({'_id': ObjectId(saran_id)})
    if saran:
        return render_template('admin/saran/detailSaran.html', saran=saran)
    else:
        return 'Artikel tidak ditemukan'

def filter_saran_by_tanggal(saran, tanggal_filter):
    filtered_saran = []
    for data in saran:
        tanggal_data = datetime.strptime(data['tanggal'], '%d-%m-%Y')
        if tanggal_data.date() == datetime.strptime(tanggal_filter, '%d-%m-%Y').date():
            filtered_saran.append(data)
    return filtered_saran

@app.route('/hapusSaran/<saran_id>', methods=['POST'])
def hapusSaran(saran_id):
    saran = db['saran'].find_one({'_id': ObjectId(saran_id)})
    path_gambar = saran['gambar']
    if os.path.exists(path_gambar):
        os.remove(path_gambar)
    db['saran'].delete_one({'_id': ObjectId(saran_id)})
    return redirect('/adminSaran')

#------------------------------------ADMIN FITUR------------------------------------#

@app.route('/adminFitur/upload', methods=['POST','GET'])
def uploadFitur():
    if 'username' in session:
        target = os.path.join(APP_ROOT, 'static/img/feature/')  #folder path
        if not os.path.isdir(target):
                os.mkdir(target)
        if request.method == 'POST':
            data = {}
            data['path'] = request.files["path"]
            data['caption'] = request.form['caption']

            for upload in request.files.getlist("path"):
                filename = secure_filename(upload.filename)
                destination = "/".join([target, filename])
                upload.save(destination)
                db.landingpage_feature.insert_one({'path': filename, 'caption': data['caption']})

            return 'Upload Successfully'
    else:
        return redirect('/login')

@app.route('/editFitur/<id>', methods=['GET', 'POST'])
def edit_data(id):
    data = db.landingpage_feature.find_one({'_id': ObjectId(id)})
    if not data:
        return 'Data tidak ditemukan'

    if request.method == 'POST':
        new_caption = request.form['caption']
        new_image = request.files['path']
        filename = secure_filename(new_image.filename)
        
        new_image.save(os.path.join(app.config['UPLOAD_FITUR'], filename))

        db.landingpage_feature.update_one(
            {'_id': ObjectId(id)},
            {'$set': {'path': filename, 'caption': new_caption}}
        )

        return 'Data berhasil diubah'

    return render_template('admin/editFitur.html', fitur=data)

@app.route('/delete/<id>', methods=['POST'])
def delete_data(id):
    data = db.landingpage_feature.find_one({'_id': ObjectId(id)})
    if not data:
        return 'Data tidak ditemukan'

    image_path = os.path.join('static/uploads', data['path'])
    if os.path.exists(image_path):
        os.remove(image_path)

    db.landingpage_feature.delete_one({'_id': ObjectId(id)})

    return 'Data berhasil dihapus'

@app.route('/adminFitur/')
def adminFitur():
    if 'username' in session:
        dataFiturWeb = db['landingpage_feature'].find({})
        return render_template("admin/adminFitur.html",fitur_list  = dataFiturWeb)
    else:
        return redirect('/login')

#------------------------------------ADMIN ARTIKEL------------------------------------#

@app.route('/adminArtikel')
def adminArtikel():
    if 'username' in session:
        artikel = db['artikel'].find()
        return render_template('admin/artikel/daftarArtikel.html', artikel=artikel)
    else:
        return redirect('/login')

@app.route('/adminArtikel/<artikel_id>')
def detailAdminArtikel(artikel_id):
    artikel = db['artikel'].find_one({'_id': ObjectId(artikel_id)})
    if artikel:
        return render_template('admin/artikel/detailArtikel.html', artikel=artikel)
    else:
        return 'Artikel tidak ditemukan'


@app.route('/adminArtikel/new', methods=['GET', 'POST'])
def tambahArtikel():
    if 'username' in session:
        if request.method == 'POST':
            judul = request.form['judul']
            isi = request.form['isi']
            image = request.files['path']
            cleaned_content = bleach.clean(isi, tags=[], strip=True)

            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_ARTIKEL'], filename))
            else:
                filename = None

            paragraphs = cleaned_content.split('\n\n')

            article = {
                'judul': judul,
                'isi': paragraphs,
                'path': filename
            }
            db['artikel'].insert_one(article)
            return redirect('/adminArtikel')
        else:
            return render_template('admin/artikel/tambahArtikel.html')
    else:
        return redirect('/login')

@app.route('/adminArtikel/edit/<artikel_id>', methods=['GET', 'POST'])
def edit_article(artikel_id):
    artikel = db['artikel'].find_one({'_id': ObjectId(artikel_id)})
    if request.method == 'POST':
        judul = request.form['judul']
        isi = request.form['isi']
        image = request.files['path']
        cleaned_content = bleach.clean(isi, tags=[], strip=True)

        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_ARTIKEL'], filename))
        else:
            filename = article['image']

        paragraphs = cleaned_content.split('\n\n')

        db['artikel'].update_one({'_id': ObjectId(artikel_id)}, {'$set': {'judul': judul, 'isi': paragraphs, 'path': filename}})
        return redirect('/adminArtikel/' + artikel_id)
    else:
        return render_template('admin/artikel/editArtikel.html', artikel=artikel)

@app.route('/adminArtikel/delete/<artikel_id>', methods=['POST'])
def delete_article(artikel_id):
    db['artikel'].delete_one({'_id': ObjectId(artikel_id)})
    return redirect('/adminArtikel')

#------------------------------------ADMIN RIWAYAT------------------------------------#

@app.route('/hapusRiwayat/<riwayat_id>', methods=['POST'])
def hapusRiwayat(riwayat_id):
    riwayat = db['riwayat'].find_one({'_id': ObjectId(riwayat_id)})
    path_gambar = riwayat['path']
    if os.path.exists(path_gambar):
        os.remove(path_gambar)
    db['riwayat'].delete_one({'_id': ObjectId(riwayat_id)})
    return redirect('/riwayat')

def filter_riwayat_by_tanggal(riwayat, tanggal_filter):
    filtered_riwayat = []
    for data in riwayat:
        tanggal_data = datetime.strptime(data['tanggal'], '%d-%m-%Y')
        if tanggal_data.date() == datetime.strptime(tanggal_filter, '%d-%m-%Y').date():
            filtered_riwayat.append(data)
    return filtered_riwayat

@app.route('/riwayat', methods=['GET'])
def riwayat():
    if 'username' in session:
        tanggal = request.args.get('tanggal')
        akurasi = request.args.get('akurasi')
        riwayat = db['riwayat'].find({})

        if tanggal:
            riwayat = db['riwayat'].find({'tanggal': tanggal})
        elif akurasi == 'high':
            riwayat = db['riwayat'].find({'akurasi': {'$gte': 75, '$lte': 100}})
        elif akurasi == 'low':
            riwayat = db['riwayat'].find({'akurasi': {'$lt': 75}})
        elif akurasi == 'all':
            riwayat = db['riwayat'].find({})

        return render_template('admin/riwayat/riwayat.html', riwayat=riwayat)
    else:
        return redirect('/login')

#------------------------------------ADMIN FAQ------------------------------------#

@app.route('/adminFaq', methods=['GET'])
def adminFaq():
    if 'username' in session:
        faqData = db['faq'].find({})
        return render_template('admin/faq/faq.html',faqData = faqData)
    else:
        return redirect('/login')

@app.route('/adminFaq/new', methods=['GET', 'POST'])
def tambahFaqData():
    if 'username' in session:
        if request.method == 'POST':
            pertanyaan = request.form['pertanyaan']
            jawaban = request.form['jawaban']

            faq = {
                'pertanyaan': pertanyaan,
                'jawaban': jawaban,
            }
            db['faq'].insert_one(faq)
            return redirect('/adminFaq')
    else:
        return redirect('/login')

@app.route('/tambahFaq', methods=['GET'])
def tambahFaq():
    if 'username' in session:
        return render_template('admin/faq/tambahFaq.html')
    else:
        return redirect('/login')

@app.route('/hapusFaq/<faq_id>', methods=['POST'])
def hapusFaq(faq_id):
    faq = db['faq'].find_one({'_id': ObjectId(faq_id)})
    db['faq'].delete_one({'_id': ObjectId(faq_id)})
    return redirect('/adminFaq')




if __name__ == "__main__":
    app.run(debug=True)
