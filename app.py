from flask import Flask, render_template, request, redirect, url_for
import os
from werkzeug.utils import secure_filename
import cv2

from locate import locate_barcode
from read import read_barcode


def get_barcode_from_img(img_path):
    barcode_imgs = locate_barcode(img_path)
    results = []
    for img in barcode_imgs:
        cv2.imshow("barcode_img", img)
        # cv2.waitKey(0)
        barcode = read_barcode(img)
        print(barcode)
        if barcode is not None:
            results.append(barcode)
    if len(results) == 0:
        print("Nie znaleziono kodu kreskowego")
        return None
    else:
        barcode = max(set(results), key=results.count)
        print(f"Znaleziono kod kreskowy: {barcode}")
        return barcode

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if a file is uploaded
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)

        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            result = get_barcode_from_img(filepath)
            if result is None:
                result = "Nie znaleziono kodu kreskowego"

            return render_template('index.html', barcode=result)

    return render_template('index.html', barcode=None)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)