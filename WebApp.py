from flask import Flask,request,render_template,jsonify
import os
from ultralytics import YOLO
import mysql.connector
import requests

app = Flask(__name__)

@app.route("/")
def helloworld():
    return render_template('index.html')

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="Arun@2002",
    database="prosol",
    auth_plugin="mysql_native_password"
)
mycursor = mydb.cursor()


def getMaterialId(noun, modifier):
    txt = "SELECT MATERIALID FROM MATERIALS WHERE NOUN='{0}' AND MODIFIER='{1}'".format(noun, modifier)
    mycursor.execute(txt)
    result = mycursor.fetchall()
    return result[0][0]


def getAttributes(materialId):
    # mycursor=getMyCursor()
    txt = "SELECT ATTRIBUTES,VAL FROM ATTVALUES WHERE MODIFIERID={0}".format(materialId)
    mycursor.execute(txt)
    result = mycursor.fetchall()
    return result

@app.route("/predict", methods=["POST"])
def predict():
    if request.method == "POST":
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
        yolo = YOLO('AugumentedBest.pt')
        results = yolo(filepath)  # Perform inference

        # Extract the class names from the results
        detected_classes = []
        for result in results:
            class_indices = result.boxes.cls.int().tolist()  # Get class indices
            detected_classes.extend([result.names[i] for i in class_indices])  # Get class names

        # Return the class names as JSON

        # consider there is only one class
        # detected=detected_classes[0]
        if (len(detected_classes) == 0):
            return jsonify({"Status": "Requested Material Not Found"})
        reqRes = []
        for i in range(len(detected_classes)):
            lst = detected_classes[i].split("-")
            dict = {"noun": lst[0], "modifier": lst[1]}

            # ListOfAtt=getMaterialInfo(lst[0],lst[1],"ATTRIBUTES")
            # fillDict(dict,ListOfAtt)
            ###########################################
            materialId = getMaterialId(lst[0], lst[1])
            result = getAttributes(materialId)
            newDict = {}
            for i in result:
                newDict[i[0]] = i[1]
            dict["Attributes"] = newDict
            reqRes.append(dict)
        return jsonify(reqRes[0])

    return jsonify({"error": "Invalid request"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0",debug=True)