var video = document.getElementById('video');
var cameraModal = document.getElementById('cameraModal');
var hasilDefault = document.getElementById("tampil");

var capturedImage = document.getElementById('capturedImage');
var labelAkurasiText = document.getElementById('akurasiLabel');
var labelNamaTanamanText = document.getElementById('namaTanamanLabel');
var accuracyText = document.getElementById('accuracy');
var namaTanamanText = document.getElementById('namaTanaman');
var namaIlmiahText = document.getElementById('namaIlmiah');
var deskripsiText = document.getElementById('deskripsi');
var khasiatText = document.getElementById('khasiat');
var khasiatLabel = document.getElementById('khasiatLabel');

var uploadContainer = document.getElementById('uploadContainer');
var imageUpload = document.getElementById('imageUpload');
var dragDropArea = document.getElementById('dragDropArea');
var resultDiv = document.getElementById('result');

var stream;


function openCameraModal() {
    cameraModal.style.display = 'block';
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(function (mediaStream) {
            stream = mediaStream;
            video.srcObject = mediaStream;
            video.play();
        })
        .catch(function (error) {
            console.log('Error accessing camera:', error);
        });
}


function closeCameraModal() {
    cameraModal.style.display = 'none';
    video.pause();
    video.src = '';
    stream.getTracks()[0].stop();
}


function captureImage() {
    var canvas = document.createElement('canvas');
    var context = canvas.getContext('2d');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    var image = canvas.toDataURL('image/jpeg');

    fetch('/scan', {
        method: 'POST',
        body: JSON.stringify({ image: image }),
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(function (response) {
        return response.json();
    })
    .then(function (data) {
        var accuracyPercentage = Math.round(data.akurasi);
        var accuracyValue = Math.floor(data.akurasi);
        if (accuracyPercentage) {
            labelAkurasiText.style.display = 'block';
            accuracyText.textContent = accuracyValue + '%';
            labelNamaTanamanText.style.display = 'block';
            namaTanamanText.textContent = data.nama;
            namaIlmiahText.textContent =  '(' + data.namailmiah + ')';
            deskripsiText.textContent = data.deskripsi;
            khasiatLabel.style.display = 'block';

            khasiatText.innerHTML = "";

            for (var i = 0; i < data.khasiat.length; i++) {
                var khasiat = data.khasiat[i];
                var listItem = document.createElement("li");
                listItem.textContent = khasiat;
                khasiatText.appendChild(listItem);
            }
            
            capturedImage.src = image;
            hasilDefault.style.display = 'none';
            capturedImage.style.display = 'block';
        } else {
            labelAkurasiText.style.display = 'none';
            namaTanamanText.textContent = 'Tanaman herbal tidak teridentifikasi';
            labelNamaTanamanText.style.display = 'none';
            capturedImage.src = image;
            hasilDefault.style.display = 'none';
            capturedImage.style.display = 'block';
            khasiatLabel.style.display = 'none';
        }
    })
    .catch(function (error) {
        console.log('Error processing image:', error);
    });

    closeCameraModal();
}


function handleImageUpload(file) {
    var reader = new FileReader();

    reader.onload = function (e) {
        var image = new Image();
        image.src = e.target.result;

        image.onload = function () {
            var canvas = document.createElement('canvas');
            var context = canvas.getContext('2d');
            canvas.width = image.width;
            canvas.height = image.height;
            context.drawImage(image, 0, 0, canvas.width, canvas.height);
            var imageData = canvas.toDataURL('image/jpeg');

            fetch('/scan', {
                method: 'POST',
                body: JSON.stringify({ image: imageData }),
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                var accuracyPercentage = Math.round(data.akurasi);
                var accuracyValue = Math.floor(data.akurasi);
                if (accuracyPercentage) {
                    labelAkurasiText.style.display = 'block';
                    accuracyText.textContent = accuracyValue + '%';
                    labelNamaTanamanText.style.display = 'block';
                    namaTanamanText.textContent = data.nama;
                    namaIlmiahText.textContent =  '(' + data.namailmiah + ')';
                    deskripsiText.textContent = data.deskripsi;
                    khasiatLabel.style.display = 'block';

                    khasiatText.innerHTML = "";

                    for (var i = 0; i < data.khasiat.length; i++) {
                        var khasiat = data.khasiat[i];
                        var listItem = document.createElement("li");
                        listItem.textContent = khasiat;
                        khasiatText.appendChild(listItem);
                    }
                    
                    capturedImage.src = imageData;
                    hasilDefault.style.display = 'none';
                    capturedImage.style.display = 'block';
                } else {
                    labelAkurasiText.style.display = 'none';
                    namaTanamanText.textContent = 'Tanaman herbal tidak teridentifikasi';
                    labelNamaTanamanText.style.display = 'none';
                    capturedImage.src = imageData;
                    hasilDefault.style.display = 'none';
                    capturedImage.style.display = 'block';
                    khasiatLabel.style.display = 'none';
                }
            })
            .catch(function (error) {
                console.log('Error processing image:', error);
            });
        };
    };

    reader.readAsDataURL(file);
}


function handleDragOver(event) {
    event.preventDefault();
    dragDropArea.classList.add('dragover');
}

function handleDragLeave(event) {
    event.preventDefault();
    dragDropArea.classList.remove('dragover');
}

function handleDrop(event) {
    event.preventDefault();
    dragDropArea.classList.remove('dragover');
    var file = event.dataTransfer.files[0];
    handleImageUpload(file);
}

imageUpload.addEventListener('change', function (event) {
    var file = event.target.files[0];
    handleImageUpload(file);
});

dragDropArea.addEventListener('dragover', handleDragOver);
dragDropArea.addEventListener('dragleave', handleDragLeave);
dragDropArea.addEventListener('drop', handleDrop);






//SARAN
document.getElementById("formSaran").addEventListener("submit", function(event) {
    event.preventDefault();
    
    var saranNama = document.getElementById("saranNama").value;
    var saranDeskripsi = document.getElementById("saranDeskripsi").value;
    var saranGambar = document.getElementById("saranGambar").files[0];
    
    if (saranNama && saranDeskripsi && saranGambar) {

        var formData = new FormData();
        formData.append("saranNama", saranNama);
        formData.append("saranDeskripsi", saranDeskripsi);
        formData.append("saranGambar", saranGambar);
        

        fetch("/tambahSaran", {
            method: "POST",
            body: formData
        })
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data.status === "success") {

                Swal.fire({
                    icon: "success",
                    title: "Sukses",
                    text: data.message,
                    confirmButtonText: "OK"
                }).then(function() {

                    location.reload();
                });
            } else {
                Swal.fire({
                    icon: "error",
                    title: "Oops...",
                    text: data.message,
                    confirmButtonText: "OK"
                });
            }
        })
        .catch(function(error) {
            Swal.fire({
                icon: "error",
                title: "Oops...",
                text: "Terjadi kesalahan. Silakan coba lagi.",
                confirmButtonText: "OK"
            });
        });
    } else {
        Swal.fire({
            icon: "error",
            title: "Oops...",
            text: "Semua kolom harus diisi!",
            confirmButtonText: "OK"
        });
    }
});

