import os
from flask import Flask, request

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route("/")
def home():
    return "Resume Shortlister is running!"

@app.route("/upload", methods=["GET", "POST"])
def upload_resume():
    if request.method == "POST":
        file = request.files["resume"]
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)
        return f"File uploaded successfully: {file.filename}"

    return '''
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="resume">
        <input type="submit" value="Upload Resume">
    </form>
    '''

if __name__ == "__main__":
    app.run(debug=True)