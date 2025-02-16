const qrScanner = {
    scannedQRCodes: [],
    init: function() {
        this.cacheDOM();
        this.bindEvents();
        this.loadScannedQRCodes();
        this.updateQRCount();
    },
    cacheDOM: function() {
        this.$startScanButton = document.getElementById('start-scan');
        this.$qrCount = document.getElementById('qr-count');
        this.$showModalButton = document.getElementById('show-modal');
        this.$qrModal = document.getElementById('qr-modal');
        this.$qrList = document.getElementById('qr-list');
        this.$uploadQRButton = document.getElementById('upload-qr');
        this.$closeButton = document.querySelector('.close');
        this.$qrVideo = document.getElementById('qr-video');
    },
    bindEvents: function() {
        this.$startScanButton.addEventListener('click', this.startScanning.bind(this));
        this.$showModalButton.addEventListener('click', this.showModal.bind(this));
        this.$uploadQRButton.addEventListener('click', this.uploadUnuploadedQRCodes.bind(this));
        this.$closeButton.addEventListener('click', this.closeModal.bind(this));
        window.addEventListener('click', this.outsideClick.bind(this));
    },
    loadScannedQRCodes: function() {
        const storedQRCodes = localStorage.getItem('scannedQRCodes');
        if (storedQRCodes) {
            this.scannedQRCodes = JSON.parse(storedQRCodes);
        }
    },
    saveScannedQRCodes: function() {
        localStorage.setItem('scannedQRCodes', JSON.stringify(this.scannedQRCodes));
    },
    updateQRCount: function() {
        this.$qrCount.textContent = this.scannedQRCodes.length;
    },
    startScanning: function() {
        navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } }).then(stream => {
            this.$qrVideo.srcObject = stream;
            this.$qrVideo.setAttribute("playsinline", true); // required to tell iOS safari we don't want fullscreen
            this.$qrVideo.play();
            requestAnimationFrame(this.tick.bind(this));
        });
    },
    tick: function() {
        if (this.$qrVideo.readyState === this.$qrVideo.HAVE_ENOUGH_DATA) {
            const canvas = document.createElement("canvas");
            canvas.width = this.$qrVideo.videoWidth;
            canvas.height = this.$qrVideo.videoHeight;
            const context = canvas.getContext("2d");
            context.drawImage(this.$qrVideo, 0, 0, canvas.width, canvas.height);
            const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
            import('jsqr').then(jsQR => {
                const code = jsQR.default(imageData.data, imageData.width, imageData.height, {
                    inversionAttempts: "dontInvert",
                });
                if (code) {
                    this.scannedQRCodes.push({ data: code.data, uploaded: false });
                    this.saveScannedQRCodes();
                    this.updateQRCount();
                    this.stopScanning();
                    return;
                }
                requestAnimationFrame(this.tick.bind(this));
            }).catch(error => {
                console.error('Error importing jsQR:', error);
            });
        } else {
            requestAnimationFrame(this.tick.bind(this));
        }
    },
    stopScanning: function() {
        const stream = this.$qrVideo.srcObject;
        const tracks = stream.getTracks();
        tracks.forEach(track => track.stop());
        this.$qrVideo.srcObject = null;
    },
    showModal: function() {
        this.updateQRList();
        this.$qrModal.style.display = 'block';
    },
    closeModal: function() {
        this.$qrModal.style.display = 'none';
    },
    outsideClick: function(event) {
        if (event.target === this.$qrModal) {
            this.closeModal();
        }
    },
    updateQRList: function() {
        this.$qrList.innerHTML = '';
        this.scannedQRCodes.forEach((qrCode, index) => {
            const listItem = document.createElement('li');
            listItem.textContent = `${index + 1}. ${qrCode.data} - ${qrCode.uploaded ? 'Uploaded' : 'Not Uploaded'}`;
            this.$qrList.appendChild(listItem);
        });
    },
    uploadUnuploadedQRCodes: function() {
        const unuploadedQRCodes = this.scannedQRCodes.filter(qrCode => !qrCode.uploaded);
        if (unuploadedQRCodes.length === 0) {
            alert('No unuploaded QR codes to upload.');
            return;
        }

        unuploadedQRCodes.forEach(qrCode => {
            fetch('/upload_qr', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ qr_data: qrCode.data })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    qrCode.uploaded = true;
                    this.saveScannedQRCodes();
                    this.updateQRList();
                } else {
                    console.error('Failed to upload QR code:', data.message);
                }
            })
            .catch(error => {
                console.error('Error uploading QR code:', error);
            });
        });
    }
};

document.addEventListener('DOMContentLoaded', function() {
    qrScanner.init();
});
