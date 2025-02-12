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
        // Implement QR code scanning functionality here
        // For now, we'll simulate scanning a QR code
        const qrData = prompt('Enter QR code data:');
        if (qrData) {
            this.scannedQRCodes.push({ data: qrData, uploaded: false });
            this.saveScannedQRCodes();
            this.updateQRCount();
        }
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
