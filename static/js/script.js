const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const capturar = document.getElementById("capturar");
const imagenInput = document.getElementById("imagen_capturada");
const form = document.getElementById("formEstres");
const archivoInput = document.querySelector('input[name="imagen"]');

// Activar cámara
if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia({ video: true })
    .then(function(stream) {
        video.srcObject = stream;
    })
    .catch(function(error) {
        console.log("Error al acceder a la cámara:", error);
        alert("No se pudo abrir la cámara. Puedes subir una imagen manualmente.");
    });
} else {
    alert("Tu navegador no permite usar la cámara.");
}

// Capturar imagen
capturar.addEventListener("click", function() {
    const contexto = canvas.getContext("2d");

    canvas.width = 320;
    canvas.height = 240;

    contexto.drawImage(video, 0, 0, canvas.width, canvas.height);

    const imagenBase64 = canvas.toDataURL("image/jpeg", 0.5);

    imagenInput.value = imagenBase64;

    alert("📸 Imagen capturada correctamente");
});

// Validar que exista imagen antes de enviar
form.addEventListener("submit", function(event) {
    const hayImagenCapturada = imagenInput.value !== "";
    const hayArchivoSubido = archivoInput.files.length > 0;

    if (!hayImagenCapturada && !hayArchivoSubido) {
        event.preventDefault();
        alert("Primero captura una imagen o sube una foto.");
    }
});