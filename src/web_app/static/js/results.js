/**
 * Results functionality for Blueberry Maturity Assessment System
 */

// Initialize results functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Results module initialized');
});

/**
 * Display results in a formatted way
 */
function displayFormattedResults(results) {
    console.log('Displaying formatted results:', results);
    
    // This function can be extended to show results in different formats
    // For now, it just logs the results
}

/**
 * Export results to different formats
 */
function exportResults(format = 'json') {
    if (!window.currentResults) {
        BlueberryApp.showAlert('No hay resultados para exportar', 'warning');
        return;
    }
    
    switch (format) {
        case 'json':
            exportToJSON();
            break;
        case 'csv':
            exportToCSV();
            break;
        case 'pdf':
            exportToPDF();
            break;
        default:
            BlueberryApp.showAlert('Formato no soportado', 'error');
    }
}

/**
 * Export results to JSON
 */
function exportToJSON() {
    const dataStr = JSON.stringify(window.currentResults, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = `blueberry_analysis_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
}

/**
 * Export results to CSV
 */
function exportToCSV() {
    if (!window.currentResults) return;
    
    const results = window.currentResults;
    const maturityAnalysis = results.maturity_analysis || {};
    const counts = maturityAnalysis.counts || {};
    
    const csvContent = [
        'Categoría,Cantidad,Porcentaje',
        `Maduro,${counts.maduro || 0},${maturityAnalysis.percentages?.maduro || 0}%`,
        `Semimaduro,${counts.semimaduro || 0},${maturityAnalysis.percentages?.semimaduro || 0}%`,
        `No maduro,${counts.no_maduro || 0},${maturityAnalysis.percentages?.no_maduro || 0}%`,
        `Total,${maturityAnalysis.total_analyzed || 0},100%`
    ].join('\n');
    
    const dataBlob = new Blob([csvContent], {type: 'text/csv'});
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = `blueberry_analysis_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
}

/**
 * Export results to PDF (placeholder)
 */
function exportToPDF() {
    BlueberryApp.showAlert('Exportación a PDF próximamente disponible', 'info');
}

/**
 * Print results
 */
function printResults() {
    if (!window.currentResults) {
        BlueberryApp.showAlert('No hay resultados para imprimir', 'warning');
        return;
    }
    
    const printWindow = window.open('', '_blank');
    const results = window.currentResults;
    
    printWindow.document.write(`
        <html>
        <head>
            <title>Análisis de Arándanos</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { text-align: center; margin-bottom: 30px; }
                .section { margin-bottom: 20px; }
                .stats { display: flex; justify-content: space-around; }
                .stat { text-align: center; }
                table { width: 100%; border-collapse: collapse; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🫐 Análisis de Madurez de Arándanos</h1>
                <p>Fecha: ${new Date().toLocaleDateString('es-ES')}</p>
            </div>
            
            <div class="section">
                <h2>Resumen del Análisis</h2>
                <div class="stats">
                    <div class="stat">
                        <h3>${results.detections || 0}</h3>
                        <p>Arándanos Detectados</p>
                    </div>
                    <div class="stat">
                        <h3>${results.maturity_analysis?.maturity_score || 0}%</h3>
                        <p>Puntuación de Madurez</p>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>Distribución de Madurez</h2>
                <table>
                    <tr>
                        <th>Categoría</th>
                        <th>Cantidad</th>
                        <th>Porcentaje</th>
                    </tr>
                    <tr>
                        <td>Maduro</td>
                        <td>${results.maturity_analysis?.counts?.maduro || 0}</td>
                        <td>${results.maturity_analysis?.percentages?.maduro || 0}%</td>
                    </tr>
                    <tr>
                        <td>Semimaduro</td>
                        <td>${results.maturity_analysis?.counts?.semimaduro || 0}</td>
                        <td>${results.maturity_analysis?.percentages?.semimaduro || 0}%</td>
                    </tr>
                    <tr>
                        <td>No maduro</td>
                        <td>${results.maturity_analysis?.counts?.no_maduro || 0}</td>
                        <td>${results.maturity_analysis?.percentages?.no_maduro || 0}%</td>
                    </tr>
                </table>
            </div>
            
        </body>
        </html>
    `);
    
    printWindow.document.close();
    printWindow.print();
}

// Export functions for global access
window.ResultsModule = {
    displayFormattedResults,
    exportResults,
    printResults
};
