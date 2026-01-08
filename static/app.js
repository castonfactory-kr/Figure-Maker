document.addEventListener('DOMContentLoaded', () => {
    const uploadArea = document.getElementById('uploadArea');
    const imageInput = document.getElementById('imageInput');
    const previewImage = document.getElementById('previewImage');
    const uploadContent = uploadArea.querySelector('.upload-content');
    const styleButtons = document.querySelectorAll('.style-btn');
    const transformBtn = document.getElementById('transformBtn');
    const resultSection = document.getElementById('resultSection');
    const originalResult = document.getElementById('originalResult');
    const characterResult = document.getElementById('characterResult');
    const downloadCharacter = document.getElementById('downloadCharacter');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const loadingText = document.getElementById('loadingText');
    const statusIndicator = document.getElementById('statusIndicator');
    const statusDot = statusIndicator.querySelector('.status-dot');
    const statusText = document.getElementById('statusText');
    const denoisingSlider = document.getElementById('denoisingStrength');
    const strengthValue = document.getElementById('strengthValue');
    const galleryGrid = document.getElementById('galleryGrid');
    const galleryEmpty = document.getElementById('galleryEmpty');
    const imageModal = document.getElementById('imageModal');
    const modalImage = document.getElementById('modalImage');
    const modalStyle = document.getElementById('modalStyle');
    const modalDownload = document.getElementById('modalDownload');
    const modalDelete = document.getElementById('modalDelete');
    const modalClose = document.getElementById('modalClose');

    let selectedFile = null;
    let selectedStyle = 'sd_character';
    let currentImageId = null;

    checkSDConnection();
    loadGallery();
    setupModal();

    async function checkSDConnection() {
        try {
            const response = await fetch('/api/transform/health');
            const data = await response.json();
            
            if (data.status === 'connected') {
                statusDot.classList.add('connected');
                statusDot.classList.remove('error');
                statusText.textContent = `Stable Diffusion 서버 연결됨 (${data.models_available}개 모델)`;
            } else {
                statusDot.classList.add('error');
                statusDot.classList.remove('connected');
                statusText.textContent = `Stable Diffusion 서버 연결 실패: ${data.message || '알 수 없는 오류'}`;
            }
        } catch (error) {
            statusDot.classList.add('error');
            statusDot.classList.remove('connected');
            statusText.textContent = 'Stable Diffusion 서버에 연결할 수 없습니다';
        }
    }

    async function loadGallery() {
        try {
            const response = await fetch('/api/transform/gallery');
            const data = await response.json();
            
            if (data.images && data.images.length > 0) {
                galleryEmpty.classList.add('hidden');
                galleryGrid.innerHTML = '';
                
                data.images.forEach(img => {
                    const item = document.createElement('div');
                    item.className = 'gallery-item';
                    item.innerHTML = `
                        <img src="${img.url}" alt="Generated character" loading="lazy">
                        <div class="gallery-item-info">
                            <span class="gallery-style">${img.style || 'unknown'}</span>
                        </div>
                    `;
                    item.addEventListener('click', () => openModal(img.id, img.url, img.style));
                    galleryGrid.appendChild(item);
                });
            } else {
                galleryEmpty.classList.remove('hidden');
                galleryGrid.innerHTML = '';
                galleryGrid.appendChild(galleryEmpty);
            }
        } catch (error) {
            console.log('Gallery load failed:', error);
        }
    }

    function setupModal() {
        modalClose.addEventListener('click', closeModal);
        imageModal.addEventListener('click', (e) => {
            if (e.target === imageModal) closeModal();
        });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeModal();
        });
        modalDelete.addEventListener('click', deleteCurrentImage);
    }

    function openModal(imageId, imageUrl, style) {
        currentImageId = imageId;
        modalImage.src = imageUrl;
        modalStyle.textContent = style || 'unknown';
        modalDownload.href = imageUrl;
        modalDownload.download = `character_${imageId}.png`;
        imageModal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    function closeModal() {
        imageModal.classList.add('hidden');
        document.body.style.overflow = '';
        currentImageId = null;
    }

    async function deleteCurrentImage() {
        if (!currentImageId) return;
        
        if (!confirm('이 이미지를 삭제하시겠습니까?')) return;
        
        try {
            const response = await fetch(`/api/transform/image/${currentImageId}/delete`, {
                method: 'POST'
            });
            
            if (response.ok) {
                closeModal();
                loadGallery();
            } else {
                const error = await response.json();
                alert('삭제 실패: ' + (error.detail || '알 수 없는 오류'));
            }
        } catch (error) {
            alert('삭제 중 오류가 발생했습니다: ' + error.message);
        }
    }

    denoisingSlider.addEventListener('input', (e) => {
        strengthValue.textContent = e.target.value;
    });

    uploadArea.addEventListener('click', () => imageInput.click());

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            handleFileSelect(file);
        }
    });

    imageInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            handleFileSelect(file);
        }
    });

    function handleFileSelect(file) {
        if (file.size > 10 * 1024 * 1024) {
            alert('파일 크기는 10MB 이하여야 합니다.');
            return;
        }

        selectedFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImage.src = e.target.result;
            previewImage.classList.remove('hidden');
            uploadContent.classList.add('hidden');
            transformBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    }

    styleButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            styleButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedStyle = btn.dataset.style;
        });
    });

    transformBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        showLoading('AI가 캐릭터를 생성하고 있습니다...');

        const formData = new FormData();
        formData.append('image', selectedFile);
        formData.append('style', selectedStyle);
        formData.append('denoising_strength', denoisingSlider.value);

        try {
            const response = await fetch('/api/transform/character', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '변환에 실패했습니다');
            }

            const data = await response.json();

            originalResult.src = data.original_url;
            characterResult.src = data.image_url;
            downloadCharacter.href = data.image_url;
            downloadCharacter.download = `character_${data.image_id}.png`;

            resultSection.classList.remove('hidden');
            resultSection.scrollIntoView({ behavior: 'smooth' });

            loadGallery();

        } catch (error) {
            alert('캐릭터 변환 실패: ' + error.message);
        } finally {
            hideLoading();
        }
    });

    function showLoading(text) {
        loadingText.textContent = text;
        loadingOverlay.classList.remove('hidden');
    }

    function hideLoading() {
        loadingOverlay.classList.add('hidden');
    }
});
