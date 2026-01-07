 젲document.addEventListener('DOMContentLoaded', () => {
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
    const generate3DBtn = document.getElementById('generate3DBtn');
    const modelSection = document.getElementById('modelSection');
    const modelStatus = document.getElementById('modelStatus');
    const modelStatusText = document.getElementById('modelStatusText');
    const modelResult = document.getElementById('modelResult');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const loadingText = document.getElementById('loadingText');

    let selectedFile = null;
    let selectedStyle = 'sd_character';
    let currentImageId = null;

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

        try {
            const response = await fetch('/api/transform/character', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Transformation failed');
            }

            const data = await response.json();
            currentImageId = data.image_id;

            originalResult.src = previewImage.src;
            characterResult.src = data.image_url;
            downloadCharacter.href = data.image_url;
            downloadCharacter.download = `character_${data.image_id}.png`;

            resultSection.classList.remove('hidden');
            resultSection.scrollIntoView({ behavior: 'smooth' });

        } catch (error) {
            alert('캐릭터 변환 실패: ' + error.message);
        } finally {
            hideLoading();
        }
    });

    generate3DBtn.addEventListener('click', async () => {
        if (!currentImageId) return;

        modelSection.classList.remove('hidden');
        modelStatus.classList.remove('hidden');
        modelResult.classList.add('hidden');
        modelSection.scrollIntoView({ behavior: 'smooth' });

        const formData = new FormData();
        formData.append('image_id', currentImageId);

        try {
            const response = await fetch('/api/transform/3d-model', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.status === 'demo_mode') {
                modelStatusText.textContent = 'Demo 모드: Meshy API 키가 설정되지 않았습니다.';
                setTimeout(() => {
                    modelResult.innerHTML = `
                        <p>3D 모델 생성을 위해 Meshy API 키가 필요합니다.</p>
                        <p class="api-note">실제 서비스에서는 이 단계에서 3D 모델 파일(.glb, .fbx)이 생성됩니다.</p>
                    `;
                    modelResult.classList.remove('hidden');
                    modelStatus.classList.add('hidden');
                }, 2000);
                return;
            }

            if (data.status === 'processing') {
                pollModelStatus(data.task_id);
            } else {
                modelStatusText.textContent = '오류: ' + (data.message || '알 수 없는 오류');
            }

        } catch (error) {
            modelStatusText.textContent = '3D 모델 생성 시작 실패: ' + error.message;
        }
    });

    async function pollModelStatus(taskId) {
        const checkStatus = async () => {
            try {
                const response = await fetch(`/api/transform/3d-model/status/${taskId}`);
                const data = await response.json();

                if (data.status === 'SUCCEEDED') {
                    modelStatus.classList.add('hidden');
                    
                    let linksHtml = '<div class="model-links">';
                    if (data.model_urls) {
                        for (const [format, url] of Object.entries(data.model_urls)) {
                            linksHtml += `<a href="${url}" class="secondary-btn" download>${format.toUpperCase()} 다운로드</a> `;
                        }
                    }
                    linksHtml += '</div>';
                    
                    if (data.thumbnail_url) {
                        linksHtml = `<img src="${data.thumbnail_url}" alt="3D Model Preview" style="max-width: 200px; border-radius: 8px; margin-bottom: 1rem;">` + linksHtml;
                    }
                    
                    document.getElementById('modelLinks').innerHTML = linksHtml;
                    modelResult.classList.remove('hidden');
                } else if (data.status === 'FAILED') {
                    modelStatusText.textContent = '3D 모델 생성 실패';
                } else {
                    modelStatusText.textContent = `3D 모델 생성 중... (${data.progress || 0}%)`;
                    setTimeout(checkStatus, 5000);
                }
            } catch (error) {
                modelStatusText.textContent = '상태 확인 실패: ' + error.message;
            }
        };

        checkStatus();
    }

    function showLoading(text) {
        loadingText.textContent = text;
        loadingOverlay.classList.remove('hidden');
    }

    function hideLoading() {
        loadingOverlay.classList.add('hidden');
    }
});
