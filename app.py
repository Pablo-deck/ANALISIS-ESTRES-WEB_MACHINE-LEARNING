from flask import Flask, render_template, request
from deepface import DeepFace
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import os
import base64
import uuid

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# =========================
# FUNCIONES
# =========================

def emocion_a_riesgo(emocion):
    emocion = emocion.lower()

    if emocion in ["happy", "neutral"]:
        return 1
    elif emocion in ["surprise"]:
        return 2
    elif emocion in ["sad", "angry", "fear", "disgust"]:
        return 3
    else:
        return 2


def calcular_puntaje_encuesta(horas_sueno, evaluaciones, cansancio, presion, horas_estudio):

    puntaje = 0

    if horas_sueno >= 7:
        puntaje += 1
    elif horas_sueno >= 5:
        puntaje += 2
    else:
        puntaje += 3

    if evaluaciones <= 1:
        puntaje += 1
    elif evaluaciones <= 3:
        puntaje += 2
    else:
        puntaje += 3

    if cansancio <= 3:
        puntaje += 1
    elif cansancio <= 7:
        puntaje += 2
    else:
        puntaje += 3

    if presion <= 3:
        puntaje += 1
    elif presion <= 7:
        puntaje += 2
    else:
        puntaje += 3

    if horas_estudio <= 3:
        puntaje += 1
    elif horas_estudio <= 6:
        puntaje += 2
    else:
        puntaje += 3

    return puntaje


def interpretar_puntaje(puntaje):
    if puntaje <= 7:
        return "Bajo"
    elif puntaje <= 11:
        return "Medio"
    else:
        return "Alto"


# =========================
# DATASET ML
# =========================

datos_entrenamiento = pd.DataFrame([
    [8, 0, 2, 2, 1, 1, "Bajo"],
    [7, 1, 3, 3, 2, 1, "Bajo"],
    [6, 1, 4, 4, 3, 1, "Bajo"],
    [6, 2, 5, 5, 3, 2, "Medio"],
    [5, 2, 6, 6, 4, 2, "Medio"],
    [5, 3, 6, 7, 4, 2, "Medio"],
    [4, 2, 7, 6, 5, 2, "Medio"],
    [4, 4, 8, 8, 5, 3, "Alto"],
    [3, 4, 9, 9, 6, 3, "Alto"],
    [2, 5, 10, 10, 7, 3, "Alto"],
    [4, 5, 9, 8, 6, 3, "Alto"]
],
columns=[
    "horas_sueno",
    "evaluaciones",
    "cansancio",
    "presion",
    "horas_estudio",
    "emocion_riesgo",
    "nivel_estres"
])

X = datos_entrenamiento[
    ["horas_sueno", "evaluaciones", "cansancio", "presion", "horas_estudio", "emocion_riesgo"]
]

y = datos_entrenamiento["nivel_estres"]

modelo = RandomForestClassifier(random_state=42)
modelo.fit(X, y)


# =========================
# ROUTES
# =========================

@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/analizar", methods=["POST"])
def analizar():

    horas_sueno = float(request.form["horas_sueno"])
    evaluaciones = int(request.form["evaluaciones"])
    cansancio = int(request.form["cansancio"])
    presion = int(request.form["presion"])
    horas_estudio = float(request.form["horas_estudio"])

    imagen = request.files.get("imagen")
    imagen_base64 = request.form.get("imagen_capturada")

    ruta_imagen = None

    # IMAGEN ARCHIVO
    if imagen and imagen.filename != "":
        filename = str(uuid.uuid4()) + ".jpg"
        ruta_imagen = os.path.join(UPLOAD_FOLDER, filename)
        imagen.save(ruta_imagen)

    # CAMARA BASE64
    elif imagen_base64:
        imagen_base64 = imagen_base64.split(",")[1]
        filename = str(uuid.uuid4()) + ".jpg"
        ruta_imagen = os.path.join(UPLOAD_FOLDER, filename)

        with open(ruta_imagen, "wb") as f:
            f.write(base64.b64decode(imagen_base64))

    else:
        return render_template("index.html", error="No se recibió imagen")

    # DEEPFACE
    resultado = DeepFace.analyze(
        img_path=ruta_imagen,
        actions=["emotion"],
        enforce_detection=False
    )

    if isinstance(resultado, list):
        resultado = resultado[0]

    emocion = resultado["dominant_emotion"]
    riesgo_facial = emocion_a_riesgo(emocion)

    # ENCUESTA
    puntaje = calcular_puntaje_encuesta(
        horas_sueno,
        evaluaciones,
        cansancio,
        presion,
        horas_estudio
    )

    nivel_encuesta = interpretar_puntaje(puntaje)

    # MACHINE LEARNING
    nuevo = pd.DataFrame([{
        "horas_sueno": horas_sueno,
        "evaluaciones": evaluaciones,
        "cansancio": cansancio,
        "presion": presion,
        "horas_estudio": horas_estudio,
        "emocion_riesgo": riesgo_facial
    }])

    nivel_ml = modelo.predict(nuevo)[0]

    return render_template(
        "index.html",
        horas_sueno=horas_sueno,
        evaluaciones=evaluaciones,
        cansancio=cansancio,
        presion=presion,
        horas_estudio=horas_estudio,
        puntaje=puntaje,
        nivel_encuesta=nivel_encuesta,
        emocion=emocion,
        riesgo_facial=riesgo_facial,
        nivel_final=nivel_ml
    )


if __name__ == "__main__":
    app.run(debug=True)