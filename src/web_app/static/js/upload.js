/**
 * Upload functionality for Blueberry Maturity Assessment System
 */

// Initialize upload functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeUploadForms();
    initializeFileInputs();
});

/**
 * Initialize upload forms
 */
function initializeUploadForms() {
    // Single upload form
    const singleUploadForm = document.getElementById('singleUploadForm');
    if (singleUploadForm) {
        singleUploadForm.addEventListener('submit', handleSingleUpload);
    }
    
    // Batch upload form
    const batchUploadForm = document.getElementById('batchUploadForm');
    if (batchUploadForm) {
        batchUploadForm.addEventListener('submit', handleBatchUpload);
    }
}

/**
 * Initialize file inputs
 */
function initializeFileInputs() {
    // Single file input
    const singleFileInput = document.getElementById('singleFileInput');
    if (singleFileInput) {
        singleFileInput.addEventListener('change', handleSingleFileSelect);
    }
    
    // Batch file input
    const batchFileInput = document.getElementById('batchFileInput');
    if (batchFileInput) {
        batchFileInput.addEventListener('change', handleBatchFileSelect);
    }
}

/**
 * Handle single file selection
 */
function handleSingleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        validateAndPreviewFile(file, 'singleUploadArea');
    }
}

/**
 * Handle batch file selection
 */
function handleBatchFileSelect(event) {
    const files = Array.from(event.target.files);
    if (files.length > 0) {
        validateAndPreviewFiles(files, 'batchUploadArea');
    }
}

/**
 * Validate and preview single file
 */
function validateAndPreviewFile(file, areaId) {
    const area = document.getElementById(areaId);
    
    // Validate file type
    if (!BlueberryApp.validateFileType(file)) {
        BlueberryApp.showAlert('Tipo de archivo no soportado. Use JPG, PNG, BMP o TIFF.', 'danger');
        return;
    }
    
    // Validate file size (max 16MB)
    if (file.size > 16 * 1024 * 1024) {
        BlueberryApp.showAlert('El archivo es demasiado grande. Máximo 16MB.', 'danger');
        return;
    }
    
    // Create preview
    BlueberryApp.createFilePreview(file)
        .then(previewUrl => {
            updateUploadArea(area, file, previewUrl);
        })
        .catch(error => {
            BlueberryApp.showAlert('Error al crear vista previa: ' + error.message, 'danger');
        });
}

/**
 * Validate and preview multiple files
 */
function validateAndPreviewFiles(files, areaId) {
    const area = document.getElementById(areaId);
    const validFiles = [];
    const invalidFiles = [];
    
    files.forEach(file => {
        if (BlueberryApp.validateFileType(file) && file.size <= 16 * 1024 * 1024) {
            validFiles.push(file);
        } else {
            invalidFiles.push(file);
        }
    });
    
    if (invalidFiles.length > 0) {
        BlueberryApp.showAlert(`${invalidFiles.length} archivo(s) no válido(s) fueron excluidos.`, 'warning');
    }
    
    if (validFiles.length > 0) {
        updateBatchUploadArea(area, validFiles);
    }
}

/**
 * Update single upload area with file preview
 */
function updateUploadArea(area, file, previewUrl) {
    const content = area.querySelector('.upload-content');
    // Preserve the existing input so the selected file remains in the form
    const fileInput = area.querySelector('input[type="file"]');
    
    content.innerHTML = `
        <div class="text-center">
            <img src="${previewUrl}" alt="Vista previa" class="file-preview mb-3">
            <h6>${file.name}</h6>
            <p class="text-muted">${BlueberryApp.formatFileSize(file.size)}</p>
            <button type="button" class="btn btn-outline-secondary btn-sm" onclick="resetUploadArea('${area.id}')">
                <i class="fas fa-times me-1"></i>Cambiar archivo
            </button>
        </div>
    `;

    // Re-append the input into the content so it stays part of the form
    if (fileInput) {
        fileInput.classList.add('d-none');
        content.appendChild(fileInput);
    }
}

/**
 * Update batch upload area with file list
 */
function updateBatchUploadArea(area, files) {
    const content = area.querySelector('.upload-content');
    // Preserve the existing input so the selected files remain in the form
    const fileInput = area.querySelector('input[type="file"]');
    
    let filesHtml = '';
    files.forEach((file, index) => {
        filesHtml += `
            <div class="d-flex align-items-center mb-2 p-2 bg-light rounded">
                <i class="fas fa-image text-primary me-2"></i>
                <div class="flex-grow-1">
                    <small class="fw-bold">${file.name}</small><br>
                    <small class="text-muted">${BlueberryApp.formatFileSize(file.size)}</small>
                </div>
            </div>
        `;
    });
    
    content.innerHTML = `
        <div class="text-center">
            <i class="fas fa-images fa-2x text-primary mb-3"></i>
            <h6>${files.length} archivo(s) seleccionado(s)</h6>
            <div class="files-list mt-3" style="max-height: 200px; overflow-y: auto;">
                ${filesHtml}
            </div>
            <button type="button" class="btn btn-outline-secondary btn-sm mt-3" onclick="resetUploadArea('${area.id}')">
                <i class="fas fa-times me-1"></i>Cambiar archivos
            </button>
        </div>
    `;

    // Re-append the input into the content so it stays part of the form
    if (fileInput) {
        fileInput.classList.add('d-none');
        content.appendChild(fileInput);
    }
}

/**
 * Reset upload area to original state
 */
function resetUploadArea(areaId) {
    const area = document.getElementById(areaId);
    const fileInput = area.querySelector('input[type="file"]');

    // Reset file input
    if (fileInput) {
        fileInput.value = '';
    }

    // Reset area content (reinsert the corresponding input so the button works)
    const content = area.querySelector('.upload-content');
    if (areaId === 'singleUploadArea') {
        content.innerHTML = `
            <i class="fas fa-cloud-upload-alt fa-3x text-muted mb-3"></i>
            <h5>Arrastra una imagen aquí o haz clic para seleccionar</h5>
            <p class="text-muted">Formatos soportados: JPG, PNG, BMP, TIFF</p>
            <input type="file" id="singleFileInput" name="file" accept=".jpg,.jpeg,.png,.bmp,.tiff" class="d-none">
            <button type="button" class="btn btn-primary" onclick="document.getElementById('singleFileInput').click()">
                <i class="fas fa-folder-open me-2"></i>Seleccionar Archivo
            </button>
        `;
    } else {
        content.innerHTML = `
            <i class="fas fa-cloud-upload-alt fa-3x text-muted mb-3"></i>
            <h5>Arrastra múltiples imágenes aquí o haz clic para seleccionar</h5>
            <p class="text-muted">Puedes seleccionar varios archivos a la vez</p>
            <input type="file" id="batchFileInput" name="files[]" accept=".jpg,.jpeg,.png,.bmp,.tiff" multiple class="d-none">
            <button type="button" class="btn btn-primary" onclick="document.getElementById('batchFileInput').click()">
                <i class="fas fa-folder-open me-2"></i>Seleccionar Archivos
            </button>
        `;
    }

    // Rebind change handlers for the newly inserted inputs
    initializeFileInputs();
}

/**
 * Handle single upload form submission
 */
async function handleSingleUpload(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const file = formData.get('file');
    
    if (!file || file.size === 0) {
        BlueberryApp.showAlert('Por favor selecciona un archivo.', 'warning');
        return;
    }
    
    try {
        BlueberryApp.showLoading();
        
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            BlueberryApp.showAlert('Análisis completado exitosamente!', 'success');
            displayResults(result.results, file, result.results?.processed_image);
        } else {
            BlueberryApp.showAlert('Error en el análisis: ' + result.error, 'danger');
        }
    } catch (error) {
        console.error('Upload error:', error);
        BlueberryApp.showAlert('Error de conexión. Intenta nuevamente.', 'danger');
    } finally {
        BlueberryApp.hideLoading();
    }
}

/**
 * Handle batch upload form submission
 */
async function handleBatchUpload(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const files = formData.getAll('files[]');
    
    if (files.length === 0 || files[0].size === 0) {
        BlueberryApp.showAlert('Por favor selecciona al menos un archivo.', 'warning');
        return;
    }
    
    try {
        BlueberryApp.showLoading();
        
        const response = await fetch('/batch_upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            BlueberryApp.showAlert(`Análisis completado: ${result.total_processed} imagen(es) procesada(s)`, 'success');
            displayBatchResults(result.results);
        } else {
            BlueberryApp.showAlert('Error en el análisis por lotes: ' + result.error, 'danger');
        }
    } catch (error) {
        console.error('Batch upload error:', error);
        BlueberryApp.showAlert('Error de conexión. Intenta nuevamente.', 'danger');
    } finally {
        BlueberryApp.hideLoading();
    }
}

/**
 * Display single analysis results
 */
function displayResults(results, file, processedImage) {
    // Store current results globally
    window.currentResults = results;
    
    // Update image display
    const analyzedImage = document.getElementById('analyzedImage');
    if (analyzedImage) {
        if (processedImage) {
            // Fallback: si no se puede cargar la imagen procesada (404 u otro), usar la vista previa local
            analyzedImage.onerror = () => {
                BlueberryApp.createFilePreview(file)
                    .then(previewUrl => {
                        analyzedImage.src = previewUrl;
                    })
                    .catch(err => console.error('Fallback preview error:', err));
            };
            analyzedImage.src = `/processed/${processedImage}?t=${Date.now()}`; // cache-buster
        } else {
            BlueberryApp.createFilePreview(file)
                .then(previewUrl => {
                    analyzedImage.src = previewUrl;
                })
                .catch(error => {
                    console.error('Error creating preview:', error);
                });
        }
    }
    
    // Update statistics
    updateStatistics(results);
    
    // Update detailed results
    updateDetailedResults(results);
    
    // Show results section
    const resultsSection = document.getElementById('results-section');
    if (resultsSection) {
        resultsSection.style.display = 'block';
        BlueberryApp.scrollToElement('results-section');
    }
}

/**
 * Display batch analysis results
 * - Muestra una galería con miniaturas y permite navegar entre cada imagen analizada
 * - Actualiza la sección de resultados con los datos de la imagen seleccionada
 */
function displayBatchResults(results) {
    if (!Array.isArray(results) || results.length === 0) {
        BlueberryApp.showAlert('No hay resultados para mostrar.', 'warning');
        return;
    }

    // Guardar resultados globales para navegación/export
    window.batchResults = results;

    // Crear/limpiar contenedor de galería en la sección de resultados
    let gallery = document.getElementById('batchGallery');
    if (!gallery) {
        gallery = document.createElement('div');
        gallery.id = 'batchGallery';
        gallery.className = 'mb-4';
        // Insertar la galería antes de la fila principal dentro de results-section
        const resultsSection = document.getElementById('results-section');
        if (resultsSection) {
            const container = resultsSection.querySelector('.container');
            if (container) container.insertBefore(gallery, container.firstChild);
        }
    }
    gallery.innerHTML = '';

    // Construir miniaturas
    results.forEach((res, idx) => {
        const thumb = document.createElement('div');
        thumb.className = 'd-inline-block me-2 mb-2';
        thumb.style.width = '120px';
        thumb.style.cursor = 'pointer';

        const img = document.createElement('img');
        img.className = 'img-fluid rounded border';
        img.style.width = '120px';
        img.alt = res.filename || `image_${idx+1}`;

        // Preferir imagen procesada si existe, sino la original subida
        if (res.processed_image) {
            img.src = `/processed/${res.processed_image}?t=${Date.now()}`;
        } else if (res.filename) {
            img.src = `/uploads/${res.filename}?t=${Date.now()}`;
        } else {
            // Placeholder
            img.src = '/static/images/placeholder.png';
        }

        // Añadir badge con número
        const badge = document.createElement('div');
        badge.innerHTML = `<small class="d-block text-center mt-1">${idx+1}</small>`;

        thumb.appendChild(img);
        thumb.appendChild(badge);

        // Click para mostrar este resultado
        thumb.addEventListener('click', () => showBatchResult(idx));

        gallery.appendChild(thumb);
    });

    // Mostrar resumen de lote
    const totalProcessed = results.length;
    const totalDetections = results.reduce((sum, result) => {
        const matured = result.maturity_analysis?.total_detected;
        const count = (typeof matured === 'number' && !isNaN(matured)) ? matured
            : ((typeof result.detections === 'number' && !isNaN(result.detections)) ? result.detections : 0);
        return sum + count;
    }, 0);
    const avgMaturityScore = results.reduce((sum, result) => {
        const dist = result.report?.maturity_analysis || result.maturity_analysis || {};
        return sum + (dist.maturity_score || 0);
    }, 0) / (totalProcessed || 1);

    BlueberryApp.showAlert(
        `Lote procesado: ${totalProcessed} imágenes, ${totalDetections} arándanos detectados, ` +
        `puntuación promedio de madurez: ${avgMaturityScore.toFixed(1)}%`,
        'info',
        8000
    );

    // Mostrar la primera imagen por defecto
    showBatchResult(0);
}

/**
 * Mostrar un resultado individual del lote por índice
 */
function showBatchResult(index) {
    const results = window.batchResults || [];
    if (!results || index < 0 || index >= results.length) return;

    const res = results[index];

    // Establecer como resultado actual global para export/print
    window.currentResults = res;

    // Actualizar imagen mostrada
    const analyzedImage = document.getElementById('analyzedImage');
    if (analyzedImage) {
        if (res.processed_image) {
            analyzedImage.onerror = () => {
                // Si falla cargar procesada, mostrar la subida original si existe
                if (res.filename) {
                    analyzedImage.src = `/uploads/${res.filename}?t=${Date.now()}`;
                }
            };
            analyzedImage.src = `/processed/${res.processed_image}?t=${Date.now()}`;
        } else if (res.filename) {
            analyzedImage.src = `/uploads/${res.filename}?t=${Date.now()}`;
        } else {
            analyzedImage.src = '/static/images/placeholder.png';
        }
    }

    // Actualizar estadísticas y detalles usando funciones existentes
    try {
        updateStatistics(res);
        updateDetailedResults(res);
    } catch (e) {
        console.error('Error actualizando UI para resultado individual:', e);
    }

    // Asegurar sección visible
    const resultsSection = document.getElementById('results-section');
    if (resultsSection) {
        resultsSection.style.display = 'block';
        BlueberryApp.scrollToElement('results-section');
    }
}

/**
 * Update statistics display
 */
function updateStatistics(results) {
    const totalDetections = document.getElementById('totalDetections');
    const maturityScore = document.getElementById('maturityScore');
    
    if (totalDetections) {
        // Prefer matured total (source of truth) to avoid mismatch with raw detections
        let count = (results.maturity_analysis && typeof results.maturity_analysis.total_detected === 'number')
            ? results.maturity_analysis.total_detected
            : undefined;
        if (typeof count !== 'number' || isNaN(count)) {
            count = (typeof results.detections === 'number' && !isNaN(results.detections)) ? results.detections : 0;
        }
        totalDetections.textContent = count;
    }
    
    if (maturityScore) {
        const dist = results.report?.maturity_analysis || results.maturity_analysis || {};
        const score = dist.maturity_score || 0;
        maturityScore.textContent = `${score}%`;
    }
    
    // Update maturity chart (safe)
    try {
        updateMaturityChart(results);
    } catch (e) {
        console.error('Error updating chart:', e);
    }
}

/**
 * Update detailed results display
 */
function updateDetailedResults(results) {
    const detailedResults = document.getElementById('detailedResults');
    if (!detailedResults) return;

    const distribution = results.report?.maturity_analysis || {};
    const detectionAnalysis = results.maturity_analysis || {};
    const detections = detectionAnalysis.detections || [];

    // Derivar conteos y porcentajes de forma robusta
    const mkCounts = () => {
        const base = { maduro: 0, semimaduro: 0, no_maduro: 0, unknown: 0 };
        detections.forEach(d => {
            const m = (d.maturity || 'unknown');
            base[m] = (base[m] || 0) + 1;
        });
        return base;
    };
    const counts = distribution.counts || mkCounts();
    const total = distribution.total_analyzed || detectionAnalysis.total_detected || detections.length || 0;
    const perc = distribution.percentages || (() => {
        const per = { maduro: 0, semimaduro: 0, no_maduro: 0, unknown: 0 };
        if (total > 0) {
            Object.keys(per).forEach(k => { per[k] = Math.round((counts[k] / total) * 1000) / 10; });
        }
        return per;
    })();

    const recommendations = results.report?.recommendations || {};

    // Colores corporativos para cada clase (solicitud):
    const COLOR_MAP = {
        maduro: '#007bff',      // Azul
        semimaduro: '#dc3545',  // Rojo
        no_maduro: '#28a745',   // Verde
        unknown: '#6c757d'
    };

    // Estadísticas agregadas
    const confidences = detections.map(d => Number(d.confidence || 0)).filter(n => !isNaN(n));
    const areas = detections.map(d => Number(d.area || 0)).filter(n => !isNaN(n));
    const avg = arr => arr.length ? arr.reduce((a,b)=>a+b,0)/arr.length : 0;
    const min = arr => arr.length ? Math.min(...arr) : 0;
    const max = arr => arr.length ? Math.max(...arr) : 0;

    const stats = {
        total: total,
        avg_conf: avg(confidences),
        min_conf: min(confidences),
        max_conf: max(confidences),
        avg_area: avg(areas),
        min_area: min(areas),
        max_area: max(areas)
    };

    // Preparar HTML detallado
    
    const buildRow = (det, idx) => {
        const [x1,y1,x2,y2] = det.bbox || [0,0,0,0];
        const w = Math.max(0, (x2 - x1));
        const h = Math.max(0, (y2 - y1));
        const cx = Math.round(x1 + w/2);
        const cy = Math.round(y1 + h/2);
        const radius = Math.floor(Math.min(w, h)/2);
        const m = det.maturity || 'unknown';
        const color = COLOR_MAP[m] || COLOR_MAP.unknown;
        return `
            <tr>
                <td class="text-muted">${idx+1}</td>
                <td><span class="badge" style="background:${color}">${m}</span></td>
                <td>${(Number(det.confidence||0)*100).toFixed(1)}%</td>
                <td>${Math.round(Number(det.area||0))}</td>
                <td>(${x1},${y1}) - (${x2},${y2})</td>
                <td>(${cx}, ${cy})</td>
                <td>${radius}px</td>
            </tr>
        `;
    };

    detailedResults.innerHTML = `
        <div class="row">
            <div class="col-lg-6">
                <h6><i class="fas fa-chart-pie me-2"></i>Distribución de Madurez</h6>
                <div class="mb-3">
                    <div class="d-flex justify-content-between mb-1">
                        <span>Maduro</span>
                        <span>${counts.maduro || 0} (${perc.maduro || 0}%)</span>
                    </div>
                    <div class="progress">
                        <div class="progress-bar" style="background:${COLOR_MAP.maduro}; width: ${perc.maduro || 0}%"></div>
                    </div>
                </div>
                <div class="mb-3">
                    <div class="d-flex justify-content-between mb-1">
                        <span>Semimaduro</span>
                        <span>${counts.semimaduro || 0} (${perc.semimaduro || 0}%)</span>
                    </div>
                    <div class="progress">
                        <div class="progress-bar" style="background:${COLOR_MAP.semimaduro}; width: ${perc.semimaduro || 0}%"></div>
                    </div>
                </div>
                <div class="mb-3">
                    <div class="d-flex justify-content-between mb-1">
                        <span>No maduro</span>
                        <span>${counts.no_maduro || 0} (${perc.no_maduro || 0}%)</span>
                    </div>
                    <div class="progress">
                        <div class="progress-bar" style="background:${COLOR_MAP.no_maduro}; width: ${perc.no_maduro || 0}%"></div>
                    </div>
                </div>
                <div class="card mt-3">
                    <div class="card-body">
                        <h6 class="mb-3"><i class="fas fa-signal me-2"></i>Resumen Estadístico</h6>
                        <div class="table-responsive">
                            <table class="table table-sm mb-0">
                                <tbody>
                                    <tr><th>Total detectados</th><td>${stats.total}</td></tr>
                                    <tr><th>Confianza promedio</th><td>${(stats.avg_conf*100).toFixed(1)}%</td></tr>
                                    <tr><th>Confianza (min - max)</th><td>${(stats.min_conf*100).toFixed(1)}% - ${(stats.max_conf*100).toFixed(1)}%</td></tr>
                                    <tr><th>Área promedio (px²)</th><td>${Math.round(stats.avg_area)}</td></tr>
                                    <tr><th>Área (min - max)</th><td>${Math.round(stats.min_area)} - ${Math.round(stats.max_area)}</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-lg-6">
                <div class="card">
                    <div class="card-body">
                        <h6 class="mb-3"><i class="fas fa-chart-line me-2"></i>Análisis Adicional</h6>
                        <div class="row g-3">
                            <div class="col-12" style="height: 240px;">
                                <canvas id="areaConfidenceChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

    `;

    // Dibujar gráfico de dispersión
    try {
        // Dispersión área vs. confianza por tipo
        const pointsByType = {
            maduro: [], semimaduro: [], no_maduro: [], unknown: []
        };
        detections.forEach(d => {
            const m = d.maturity || 'unknown';
            const area = Number(d.area || 0);
            const conf = Number(d.confidence || 0);
            if (!isNaN(area) && !isNaN(conf)) {
                pointsByType[m]?.push({ x: area, y: conf });
            }
        });
        const areaCtx = document.getElementById('areaConfidenceChart');
        if (areaCtx) {
            if (window._areaChart && typeof window._areaChart.destroy === 'function') window._areaChart.destroy();
            window._areaChart = new Chart(areaCtx, {
                type: 'scatter',
                data: {
                    datasets: [
                        { label: 'Maduro', data: pointsByType.maduro, borderColor: COLOR_MAP.maduro, backgroundColor: COLOR_MAP.maduro },
                        { label: 'Semimaduro', data: pointsByType.semimaduro, borderColor: COLOR_MAP.semimaduro, backgroundColor: COLOR_MAP.semimaduro },
                        { label: 'No maduro', data: pointsByType.no_maduro, borderColor: COLOR_MAP.no_maduro, backgroundColor: COLOR_MAP.no_maduro },
                        { label: 'Unknown', data: pointsByType.unknown, borderColor: COLOR_MAP.unknown, backgroundColor: COLOR_MAP.unknown }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { title: { display: true, text: 'Área (px²)' }, grid: { color: 'rgba(0,0,0,0.05)' } },
                        y: { title: { display: true, text: 'Confianza' }, min: 0, max: 1, grid: { color: 'rgba(0,0,0,0.05)' } }
                    }
                }
            });
        }
    } catch (e) {
        console.error('Error creando gráfico de dispersión:', e);
    }
}

/**
 * Update maturity chart
 */
function updateMaturityChart(results) {
    const maturityAnalysis = results.report?.maturity_analysis || results.maturity_analysis || {};
    const canvas = document.getElementById('maturityChart');
    
    if (!canvas) return;
    
    // Destroy existing chart safely in case a DOM element with same id created a global
    if (window.maturityChart && typeof window.maturityChart.destroy === 'function') {
        window.maturityChart.destroy();
    }
    
    const data = {
        labels: ['Maduro', 'Semimaduro', 'No maduro'],
        datasets: [{
            data: [
                maturityAnalysis.counts?.maduro || 0,
                maturityAnalysis.counts?.semimaduro || 0,
                maturityAnalysis.counts?.no_maduro || 0
            ],
            backgroundColor: ['#28a745', '#ffc107', '#dc3545'],
            borderWidth: 2,
            borderColor: '#fff'
        }]
    };
    
    const config = {
        type: 'doughnut',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    };
    
    window.maturityChart = new Chart(canvas, config);
}
