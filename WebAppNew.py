from flask import Flask, request, jsonify,render_template
import os
from ultralytics import YOLO
import mysql.connector

app = Flask(__name__)

# Database connection
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="Arun@2002",
    database="prosol",
    auth_plugin="mysql_native_password"
)
mycursor = mydb.cursor()

@app.route("/")
def homePage():
    return render_template("index2.html")

def getMaterialId(noun, modifier):
    txt = "SELECT MATERIALID FROM MATERIALS WHERE NOUN='{0}' AND MODIFIER='{1}'".format(noun, modifier)
    mycursor.execute(txt)
    result = mycursor.fetchall()
    return result[0][0]

def getAttributes(materialId):
    txt = "SELECT ATTRIBUTES,VAL FROM ATTVALUES WHERE MODIFIERID={0}".format(materialId)
    mycursor.execute(txt)
    result = mycursor.fetchall()
    return result

@app.route("/predict", methods=["POST"])
def predict():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    # Save the uploaded file
    basepath = os.path.dirname(__file__)
    upload_folder = os.path.join(basepath, 'uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    filepath = os.path.join(upload_folder, file.filename)
    file.save(filepath)  # Save the image file

    # Run YOLOv8 inference
    yolo = YOLO('best.pt')
    results = yolo.predict(filepath)  # Perform inference

    # Extract the class names from the results
    detected_classes = []
    for result in results:
        class_indices = result.boxes.cls.int().tolist()  # Get class indices
        detected_classes.extend([result.names[i] for i in class_indices])  # Get class names

    if len(detected_classes) == 0:
        return jsonify({"Status": "Requested Material Not Found"})

    reqRes = []
    for detected_class in detected_classes:
        lst = detected_class.split("-")
        noun, modifier = lst[0], lst[1]
        dict = {"noun": noun, "modifier": modifier}

        # Get material attributes
        materialId = getMaterialId(noun, modifier)
        result = getAttributes(materialId)
        attributes_dict = {i[0]: i[1] for i in result}
        dict["Attributes"] = attributes_dict
        reqRes.append(dict)
    print("Crossed all points, NearBy success!")
    return jsonify(reqRes[0])

if __name__ == "__main__":
    app.run(host="0.0.0.0",debug=True)