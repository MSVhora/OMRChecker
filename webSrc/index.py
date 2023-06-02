import os
import time
from flask import *
from flask_json import FlaskJSON, json_response
import fitz
import io
from PIL import Image
from main import processOMRFile

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "../uploads")
os.mkdir(UPLOAD_FOLDER)
os.mkdir(os.path.join(UPLOAD_FOLDER, "images"))
ALLOWED_EXTENSIONS = set(["pdf"])


app = Flask(__name__)
json = FlaskJSON()
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1] in ALLOWED_EXTENSIONS


@app.route("/", methods=["POST"])
def calcMarks():
    # check if the post request has the file part
    if "file" not in request.files:
        return "No file part", 400

    file = request.files["file"]
    exam = request.form["exam"]

    if file.filename == "":
        return "No selected file", 400

    if file and allowed_file(file.filename):
        fileName = f"{time.time()}_{file.filename}"
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], fileName))
        result = extractImagesFromPDF(
            exam,
            os.path.join(app.config["UPLOAD_FOLDER"], fileName),
            os.path.splitext(fileName)[0],
        )
        return json_response(status_=200, data_=result)
    else:
        return "Invalid file format", 400


def extractImagesFromPDF(exam, filePath, fileName):
    result = []
    pdfFile = fitz.open(filePath)
    for pageIndex in range(len(pdfFile)):
        page = pdfFile[pageIndex]
        for imageIndex, img in enumerate(page.get_images(), start=1):
            xref = img[0]
            baseImage = pdfFile.extract_image(xref)
            imageBytes = baseImage["image"]
            imageExt = baseImage["ext"]
            image = Image.open(io.BytesIO(imageBytes))
            imageDirectoryPath = os.path.join(
                app.config["UPLOAD_FOLDER"], "images", fileName
            )
            os.mkdir(imageDirectoryPath)
            omrPath = os.path.join(
                imageDirectoryPath,
                f"{pageIndex+1}_{imageIndex}.{imageExt}",
            )
            image.save(
                open(
                    omrPath,
                    "wb",
                )
            )
            result.append(processOMRFile(exam, omrPath))
    return result
