/**
 * Funcionalidad de historial de análisis
 */

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar historial
    loadHistory();
    
    // Evento para exportar a CSV
    const exportBtn = document.getElementById('exportCsvBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportToCsv);
    }
});

// Estado global para paginación
let currentPage = 1;
const perPage = 10;

/**
 * Cargar historial de análisis
 */
async function loadHistory(page = 1) {
    try {
        const response = await fetch(`/history?page=${page}&per_page=${perPage}`);
        const data = await response.json();
        
        if (data.success) {
            displayHistory(data.data);
            updatePagination(data.page, data.per_page, data.data.length);
        } else {
            BlueberryApp.showAlert('Error cargando historial: ' + data.error, 'danger');
        }
    } catch (error) {
        console.error('Error loading history:', error);
        BlueberryApp.showAlert('Error de conexión', 'danger');
    }
}

/**
 * Mostrar historial en la tabla
 */
function displayHistory(records) {
    const tbody = document.querySelector('#historyTable tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    records.forEach(record => {
        const tr = document.createElement('tr');
        tr.setAttribute('data-id', record.id);
        
        // Imagen en miniatura
        let imgSrc = record.processed_filename 
            ? `/processed/${record.processed_filename}`
            : `/uploads/${record.filename}`;
        
        // Distribución de madurez
        const dist = record.maturity_distribution || {};
        const counts = dist.counts || {};
        
        tr.innerHTML = `
            <td>
                <img src="${imgSrc}" alt="Análisis ${record.id}" 
                     class="img-thumbnail" style="width: 100px; height: 100px; object-fit: cover;"
                     data-bs-toggle="modal" data-bs-target="#imageModal"
                     onclick="showFullImage('${imgSrc}')">
            </td>
            <td>${record.created_at}</td>
            <td>${record.total_detections || 0}</td>
            <td>${counts.maduro || 0}</td>
            <td>${counts.semimaduro || 0}</td>
            <td>${counts.no_maduro || 0}</td>
            <td>${record.maturity_score}%</td>
            <td>
                <div class="btn-group">
                    <button class="btn btn-sm btn-success" onclick="exportRecord(${record.id})" title="Exportar registro">
                        <i class="fas fa-file-csv"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteRecord(${record.id})" title="Eliminar registro">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;
        
        tbody.appendChild(tr);
    });
    
    // Actualizar contador
    const totalRecords = document.getElementById('totalRecords');
    if (totalRecords) {
        totalRecords.textContent = records.length;
    }
}

/**
 * Actualizar paginación
 */
function updatePagination(page, perPage, totalItems) {
    const pagination = document.getElementById('historyPagination');
    if (!pagination) return;
    
    const totalPages = Math.ceil(totalItems / perPage);
    currentPage = page;
    
    let html = '';
    
    // Botón anterior
    html += `
        <li class="page-item ${page <= 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="loadHistory(${page-1})">&laquo;</a>
        </li>
    `;
    
    // Páginas
    for (let i = 1; i <= totalPages; i++) {
        html += `
            <li class="page-item ${i === page ? 'active' : ''}">
                <a class="page-link" href="#" onclick="loadHistory(${i})">${i}</a>
            </li>
        `;
    }
    
    // Botón siguiente
    html += `
        <li class="page-item ${page >= totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="loadHistory(${page+1})">&raquo;</a>
        </li>
    `;
    
    pagination.innerHTML = html;
}

/**
 * Exportar historial a CSV
 */
async function exportToCsv() {
    try {
        BlueberryApp.showLoading('Generando archivo CSV...');
        
        const response = await fetch('/export');
        
        if (response.ok) {
            // Crear link temporal para descarga
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `analisis_arandanos_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
            
            BlueberryApp.showAlert('Archivo CSV generado correctamente', 'success');
        } else {
            const error = await response.json();
            BlueberryApp.showAlert('Error exportando: ' + error.error, 'danger');
        }
    } catch (error) {
        console.error('Export error:', error);
        BlueberryApp.showAlert('Error generando archivo CSV', 'danger');
    } finally {
        BlueberryApp.hideLoading();
    }
}

/**
 * Exportar un registro individual
 */
async function exportRecord(id) {
    try {
        BlueberryApp.showLoading('Generando archivo CSV...');
        
        const response = await fetch(`/export/${id}`);
        
        if (response.ok) {
            // Crear link temporal para descarga
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `analisis_arandano_${id}_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
            
            BlueberryApp.showAlert('Archivo CSV generado correctamente', 'success');
        } else {
            const error = await response.json();
            BlueberryApp.showAlert('Error exportando: ' + error.error, 'danger');
        }
    } catch (error) {
        console.error('Export error:', error);
        BlueberryApp.showAlert('Error generando archivo CSV', 'danger');
    } finally {
        BlueberryApp.hideLoading();
    }
}

/**
 * Eliminar un registro
 */
async function deleteRecord(id) {
    if (!confirm('¿Estás seguro de que deseas eliminar este registro? Esta acción no se puede deshacer.')) {
        return;
    }

    try {
        const row = document.querySelector(`tr[data-id="${id}"]`);
        if (row) {
            // Añadir clase de animación de fade out
            row.style.transition = 'opacity 0.3s ease';
            row.style.opacity = '0.5';
        }
        
        const response = await fetch(`/history/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            if (row) {
                // Remover la fila con animación
                row.addEventListener('transitionend', () => {
                    row.remove();
                });
                row.style.opacity = '0';
            }
            BlueberryApp.showAlert('Registro eliminado correctamente', 'success');
            // Recargar la página actual del historial después de un pequeño retraso
            setTimeout(() => loadHistory(currentPage), 300);
        } else {
            if (row) {
                // Restaurar la opacidad si hay error
                row.style.opacity = '1';
            }
            const error = await response.json();
            BlueberryApp.showAlert('Error eliminando registro: ' + error.error, 'danger');
        }
    } catch (error) {
        console.error('Delete error:', error);
        BlueberryApp.showAlert('Error de conexión', 'danger');
    }
}

/**
 * Mostrar imagen completa en modal
 */
function showFullImage(src) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'imageModal';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Vista Completa</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body text-center">
                    <img src="${src}" class="img-fluid" alt="Vista completa">
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
    
    modal.addEventListener('hidden.bs.modal', function () {
        modal.remove();
    });
}