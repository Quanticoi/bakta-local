/**
 * PUC Minas - Bakta Web Application
 * JavaScript principal da interface
 */

// ============== CONFIGURAÇÕES ==============
const API_BASE_URL = ''; // Mesma origem
const POLLING_INTERVAL = 3000; // 3 segundos

// ============== ESTADO GLOBAL ==============
let currentJobId = null;
let pollingTimer = null;
let selectedSource = null; // 'upload' ou 'template'
let selectedFile = null;

// ============== INICIALIZAÇÃO ==============
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

function initializeApp() {
    loadTemplates();
    loadStats();
    loadJobs();
    setupEventListeners();

    // Atualizar estatísticas periodicamente
    setInterval(loadStats, 30000);
    setInterval(loadJobs, 10000);
}

// ============== EVENT LISTENERS ==============
function setupEventListeners() {
    // Upload de arquivo
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');

    uploadArea.addEventListener('click', () => fileInput.click());

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

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    // Remover arquivo selecionado
    document.getElementById('remove-file').addEventListener('click', () => {
        selectedFile = null;
        selectedSource = null;
        updateUI();
    });

    // Iniciar anotação
    document.getElementById('btn-annotate').addEventListener('click', startAnnotation);
}

// ============== API CALLS ==============
async function apiGet(endpoint) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`API GET Error (${endpoint}):`, error);
        showToast('Erro', `Falha ao comunicar com o servidor: ${error.message}`, 'danger');
        throw error;
    }
}

async function apiPost(endpoint, data) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || `HTTP ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`API POST Error (${endpoint}):`, error);
        showToast('Erro', error.message, 'danger');
        throw error;
    }
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE_URL}/api/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || `HTTP ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Upload Error:', error);
        showToast('Erro', `Falha no upload: ${error.message}`, 'danger');
        throw error;
    }
}

// ============== FUNÇÕES PRINCIPAIS ==============
async function loadTemplates() {
    try {
        const data = await apiGet('/api/templates');
        const templates = Array.isArray(data.templates) ? data.templates : [];
        renderTemplates(templates);
    } catch (error) {
        document.getElementById('templates-container').innerHTML = `
            <div class="col-12 text-center text-muted py-3">
                <i class="bi bi-exclamation-triangle"></i> Erro ao carregar templates
            </div>
        `;
    }
}

function renderTemplates(templates) {
    const container = document.getElementById('templates-container');

    if (templates.length === 0) {
        container.innerHTML = `
            <div class="col-12 text-center text-muted py-3">
                <i class="bi bi-inbox"></i> Nenhum template disponível
            </div>
        `;
        return;
    }

    container.innerHTML = templates.map(t => `
        <div class="col-md-4 mb-2">
            <div class="card template-card h-100" data-filename="${t.name}" data-source="template">
                <div class="card-body p-3">
                    <div class="d-flex align-items-center">
                        <i class="bi bi-file-earmark-text text-primary fs-4 me-2"></i>
                        <div>
                            <h6 class="mb-0 text-truncate" style="max-width: 150px;" title="${t.name}">${t.name}</h6>
                            <small class="text-muted">${formatBytes(t.size)}</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `).join('');

    // Adicionar event listeners
    document.querySelectorAll('.template-card').forEach(card => {
        card.addEventListener('click', () => {
            document.querySelectorAll('.template-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');

            selectedSource = 'template';
            selectedFile = {
                filename: card.dataset.filename,
                name: card.dataset.filename
            };
            updateUI();
        });
    });
}

async function handleFileSelect(file) {
    // Validar extensão
    const allowedExts = ['fasta', 'fna', 'fa', 'fas'];
    const ext = file.name.split('.').pop().toLowerCase();

    if (!allowedExts.includes(ext)) {
        showToast('Erro', 'Tipo de arquivo não permitido. Use: .fasta, .fna, .fa, .fas', 'danger');
        return;
    }

    try {
        showToast('Upload', 'Enviando arquivo...', 'info');
        const result = await uploadFile(file);

        selectedSource = 'upload';
        selectedFile = {
            filename: result.filename,
            name: result.original_name,
            size: result.size
        };

        // Limpar seleção de template
        document.querySelectorAll('.template-card').forEach(c => c.classList.remove('selected'));

        updateUI();
        showToast('Sucesso', 'Arquivo enviado com sucesso!', 'success');
    } catch (error) {
        console.error('File upload error:', error);
    }
}

function updateUI() {
    const uploadArea = document.getElementById('upload-area');
    const selectedFileDiv = document.getElementById('selected-file');
    const filenameSpan = document.getElementById('filename');
    const btnAnnotate = document.getElementById('btn-annotate');

    if (selectedFile) {
        uploadArea.classList.add('d-none');
        selectedFileDiv.classList.remove('d-none');
        filenameSpan.textContent = `${selectedFile.name} (${formatBytes(selectedFile.size || 0)})`;
        btnAnnotate.disabled = false;
    } else {
        uploadArea.classList.remove('d-none');
        selectedFileDiv.classList.add('d-none');
        btnAnnotate.disabled = true;
        document.getElementById('file-input').value = '';
    }
}

async function startAnnotation() {
    if (!selectedFile) {
        showToast('Erro', 'Selecione um arquivo ou template primeiro', 'warning');
        return;
    }

    const prefix = document.getElementById('prefix-input').value.trim();

    const btn = document.getElementById('btn-annotate');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Iniciando...';

    try {
        const data = {
            source: selectedSource,
            filename: selectedFile.filename,
            prefix: prefix || undefined
        };

        const result = await apiPost('/api/annotate', data);

        currentJobId = result.job_id;
        showProgressSection();
        startPolling(currentJobId);

        showToast('Sucesso', `Anotação iniciada! Job ID: ${currentJobId}`, 'success');

        // Limpar seleção
        selectedFile = null;
        selectedSource = null;
        document.getElementById('prefix-input').value = '';
        document.querySelectorAll('.template-card').forEach(c => c.classList.remove('selected'));
        updateUI();

    } catch (error) {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-play-fill"></i> Iniciar Anotação';
    }
}

function showProgressSection() {
    document.getElementById('progress-section').classList.remove('d-none');
    document.getElementById('progress-jobid').textContent = `Job ID: ${currentJobId}`;
    document.getElementById('progress-bar').style.width = '0%';
    document.getElementById('progress-bar').textContent = '0%';
}

function startPolling(jobId) {
    if (pollingTimer) {
        clearInterval(pollingTimer);
    }

    pollingTimer = setInterval(() => checkJobStatus(jobId), POLLING_INTERVAL);
}

async function checkJobStatus(jobId) {
    try {
        const data = await apiGet(`/api/jobs/${jobId}/status`);
        updateProgress(data);

        if (data.status === 'completed' || data.status === 'error') {
            clearInterval(pollingTimer);
            pollingTimer = null;

            if (data.status === 'completed') {
                onJobComplete(data);
            } else {
                onJobError(data);
            }

            loadJobs();
            loadStats();
        }
    } catch (error) {
        console.error('Status check error:', error);
    }
}

function updateProgress(data) {
    const progressBar = document.getElementById('progress-bar');
    const messageEl = document.getElementById('progress-message');
    const spinner = document.getElementById('progress-spinner');

    const progress = data.progress || 0;
    progressBar.style.width = `${progress}%`;
    progressBar.textContent = `${progress}%`;

    if (data.message) {
        messageEl.textContent = data.message;
    }

    if (data.status === 'completed') {
        progressBar.classList.remove('progress-bar-animated');
        spinner.classList.add('d-none');
        messageEl.innerHTML = '<i class="bi bi-check-circle text-success"></i> Concluído!';
    } else if (data.status === 'error') {
        progressBar.classList.add('bg-danger');
        spinner.classList.add('d-none');
        messageEl.innerHTML = `<i class="bi bi-x-circle text-danger"></i> Erro: ${data.message}`;
    }
}

function onJobComplete(data) {
    showToast('Sucesso', 'Anotação concluída com sucesso!', 'success');

    // Mostrar seção de visualização
    document.getElementById('visualization-section').classList.remove('d-none');

    if (data.result) {
        renderVisualization(data.result);
    }
}

function onJobError(data) {
    showToast('Erro', `Anotação falhou: ${data.message}`, 'danger');
}

// ============== CARREGAMENTO DE DADOS ==============
async function loadStats() {
    try {
        const data = await apiGet('/api/stats');

        document.getElementById('stat-jobs').textContent = data.total_jobs;
        document.getElementById('stat-completed').textContent = data.completed;
        document.getElementById('stat-cds').textContent = formatNumber(data.total_cds_annotated);
        document.getElementById('stat-pending').textContent =
            data.total_jobs - data.completed - data.errors;
    } catch (error) {
        console.error('Load stats error:', error);
    }
}

async function loadJobs() {
    try {
        const data = await apiGet('/api/jobs');
        renderJobs(data.jobs);
    } catch (error) {
        console.error('Load jobs error:', error);
    }
}

function renderJobs(jobs) {
    const container = document.getElementById('jobs-container');

    if (jobs.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-5">
                <i class="bi bi-inbox" style="font-size: 3rem;"></i>
                <p class="mt-3">Nenhum job executado ainda</p>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="list-group">
            ${jobs.map(job => renderJobItem(job)).join('')}
        </div>
    `;

    // Adicionar event listeners para botões
    document.querySelectorAll('.btn-view-job').forEach(btn => {
        btn.addEventListener('click', () => viewJobDetails(btn.dataset.jobId));
    });

    document.querySelectorAll('.btn-delete-job').forEach(btn => {
        btn.addEventListener('click', () => deleteJob(btn.dataset.jobId));
    });

    document.querySelectorAll('.btn-download').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            downloadFile(btn.dataset.jobId, btn.dataset.fileType);
        });
    });
}

function renderJobItem(job) {
    const status = job.status || 'unknown';
    const stats = job.stats || {};
    const runtimeStatus = job.runtime_status || {};

    const statusClass = {
        'completed': 'status-completed',
        'running': 'status-running',
        'error': 'status-error'
    }[status] || '';

    const statusIcon = {
        'completed': 'bi-check-circle-fill text-success',
        'running': 'bi-arrow-repeat text-warning',
        'error': 'bi-x-circle-fill text-danger'
    }[status] || 'bi-question-circle text-muted';

    const formattedDate = job.job_id ?
        `${job.job_id.substring(0, 4)}-${job.job_id.substring(4, 6)}-${job.job_id.substring(6, 8)} ${job.job_id.substring(9, 11)}:${job.job_id.substring(11, 13)}` :
        'Data desconhecida';

    return `
        <div class="list-group-item job-item ${statusClass} fade-in">
            <div class="d-flex w-100 justify-content-between align-items-center">
                <div class="d-flex align-items-center">
                    <i class="bi ${statusIcon} fs-4 me-3"></i>
                    <div>
                        <h6 class="mb-1">Job ${job.job_id}</h6>
                        <small class="text-muted">
                            <i class="bi bi-calendar"></i> ${formattedDate}
                            ${runtimeStatus.message ? `| ${runtimeStatus.message}` : ''}
                        </small>
                    </div>
                </div>
                <div class="d-flex align-items-center">
                    ${status === 'completed' ? `
                        <div class="me-3">
                            <span class="badge badge-cds me-1" title="CDS">${stats.cds || 0}</span>
                            <span class="badge badge-trna me-1" title="tRNAs">${stats.trnas || 0}</span>
                            <span class="badge badge-rrna" title="rRNAs">${stats.rrnas || 0}</span>
                        </div>
                        <div class="dropdown me-2">
                            <button class="btn btn-sm btn-outline-primary dropdown-toggle" 
                                    data-bs-toggle="dropdown">
                                <i class="bi bi-download"></i> Download
                            </button>
                            <ul class="dropdown-menu">
                                    <li><a class="dropdown-item btn-download" href="#" 
                                       data-job-id="${job.job_id}" data-file-type="json">JSON</a></li>
                                    <li><a class="dropdown-item btn-download" href="#" 
                                       data-job-id="${job.job_id}" data-file-type="gff3">GFF3</a></li>
                                    <li><a class="dropdown-item btn-download" href="#" 
                                       data-job-id="${job.job_id}" data-file-type="faa">Proteínas (FAA)</a></li>
                                    <li><a class="dropdown-item btn-download" href="#" 
                                       data-job-id="${job.job_id}" data-file-type="ffn">Features (FFN)</a></li>
                                    <li><a class="dropdown-item btn-download" href="#" 
                                       data-job-id="${job.job_id}" data-file-type="txt">Resumo</a></li>
                            </ul>
                        </div>
                    ` : ''}
                    <button class="btn btn-sm btn-outline-info btn-view-job me-2" 
                            data-job-id="${job.job_id}">
                        <i class="bi bi-eye"></i> Ver
                    </button>
                    <button class="btn btn-sm btn-outline-danger btn-delete-job" 
                            data-job-id="${job.job_id}">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
        </div>
    `;
}

// ============== AÇÕES ==============
async function viewJobDetails(jobId) {
    try {
        const job = await apiGet(`/api/jobs/${jobId}`);

        const stats = job.stats || {};
        const files = job.files || {};

        let filesHtml = '';
        if (Object.keys(files).length > 0) {
            filesHtml = `
                <h6 class="mt-4">Arquivos Gerados</h6>
                <div class="list-group">
                    ${Object.entries(files).map(([ext, info]) => `
                        <div class="list-group-item d-flex justify-content-between align-items-center">
                            <div>
                                <strong>.${ext}</strong>
                                <small class="text-muted d-block">${info.description}</small>
                            </div>
                            <span class="badge bg-secondary">${formatBytes(info.size)}</span>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        const content = `
            <div class="row">
                <div class="col-md-6">
                    <h6>Informações Gerais</h6>
                    <table class="table table-sm">
                        <tr><td><strong>Job ID:</strong></td><td>${job.job_id}</td></tr>
                        <tr><td><strong>Status:</strong></td><td>
                            <span class="badge bg-${job.status === 'completed' ? 'success' : 'danger'}">
                                ${job.status}
                            </span>
                        </td></tr>
                        <tr><td><strong>Prefixo:</strong></td><td>${job.prefix || '-'}</td></tr>
                        <tr><td><strong>Diretório:</strong></td><td><code>${job.output_dir}</code></td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6>Estatísticas</h6>
                    <table class="table table-sm">
                        <tr><td><strong>Tamanho:</strong></td><td>${formatNumber(stats.genome_size || 0)} bp</td></tr>
                        <tr><td><strong>GC Content:</strong></td><td>${(stats.gc_content || 0).toFixed(2)}%</td></tr>
                        <tr><td><strong>Contigs:</strong></td><td>${stats.n_contigs || 0}</td></tr>
                        <tr><td><strong>N50:</strong></td><td>${formatNumber(stats.n50 || 0)}</td></tr>
                    </table>
                </div>
            </div>
            <div class="row mt-3">
                <div class="col-12">
                    <h6>Features Anotadas</h6>
                    <div class="d-flex flex-wrap gap-2">
                        <span class="badge badge-cds fs-6"><i class="bi bi-grid"></i> CDS: ${stats.cds || 0}</span>
                        <span class="badge badge-gene fs-6"><i class="bi bi-activity"></i> Genes: ${stats.genes || 0}</span>
                        <span class="badge badge-trna fs-6"><i class="bi bi-bezier2"></i> tRNAs: ${stats.trnas || 0}</span>
                        <span class="badge badge-rrna fs-6"><i class="bi bi-circle"></i> rRNAs: ${stats.rrnas || 0}</span>
                        <span class="badge badge-ncrna fs-6"><i class="bi bi-bezier"></i> ncRNAs: ${stats.ncrnas || 0}</span>
                    </div>
                </div>
            </div>
            <div class="row mt-3">
                <div class="col-12">
                    <h6>Visualização do Job</h6>
                    <div id="job-modal-visualization"></div>
                </div>
            </div>
            ${filesHtml}
        `;

        document.getElementById('job-modal-content').innerHTML = content;

        const modal = new bootstrap.Modal(document.getElementById('jobModal'));
        modal.show();

        // Exibe o gráfico imediatamente dentro do modal para evitar confusão de navegação.
        renderVisualization(job, 'job-modal-visualization');

        // Também atualiza a seção de visualização abaixo da lista de resultados.
        document.getElementById('visualization-section').classList.remove('d-none');
        renderVisualization(job, 'visualization-container');
        document.getElementById('visualization-section').scrollIntoView({ behavior: 'smooth', block: 'start' });

    } catch (error) {
        console.error('View job error:', error);
    }
}

async function deleteJob(jobId) {
    if (!confirm(`Tem certeza que deseja remover o job ${jobId}?`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/jobs/${jobId}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Falha ao remover job');

        showToast('Sucesso', 'Job removido com sucesso!', 'success');
        loadJobs();
        loadStats();
    } catch (error) {
        showToast('Erro', 'Falha ao remover job', 'danger');
    }
}

function downloadFile(jobId, fileType) {
    window.open(`${API_BASE_URL}/api/jobs/${jobId}/files/${fileType}`, '_blank');
}

// ============== UTILITÁRIOS ==============
function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function showToast(title, message, type = 'info') {
    const container = document.querySelector('.toast-container');
    const toastId = 'toast-' + Date.now();

    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type} border-0" 
             id="${toastId}" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <strong>${title}</strong><br>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                        data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', toastHtml);

    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: 5000 });
    toast.show();

    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

// ============== VISUALIZAÇÃO ==============
function renderVisualization(jobData, containerId = 'visualization-container') {
    const container = document.getElementById(containerId);
    if (!container) {
        return;
    }

    const stats = jobData.stats || {};
    const files = jobData.files || {};

    const cds = stats.cds || 0;
    const genes = stats.genes || 0;
    const trnas = stats.trnas || 0;
    const rrnas = stats.rrnas || 0;
    const ncrnas = stats.ncrnas || 0;
    const total = Math.max(cds + trnas + rrnas + ncrnas, 1);

    const cdsPct = Math.round((cds / total) * 100);
    const trnaPct = Math.round((trnas / total) * 100);
    const rrnaPct = Math.round((rrnas / total) * 100);
    const ncrnaPct = Math.max(100 - cdsPct - trnaPct - rrnaPct, 0);

    const svgAvailable = !!files.svg;
    const pngAvailable = !!files.png;
    const plotFileType = svgAvailable ? 'svg' : (pngAvailable ? 'png' : null);
    const plotUrl = plotFileType ? `${API_BASE_URL}/api/jobs/${jobData.job_id}/files/${plotFileType}` : '';

    const circularPlotHtml = plotFileType ? `
        <div class="viz-circular-wrap">
            <h6 class="mb-3">Mapa circular de sítios anotados</h6>
            <div class="viz-circular-frame">
                <img class="viz-circular-image" src="${plotUrl}" alt="Plot circular do job ${jobData.job_id}">
            </div>
            <div class="mt-3">
                <a class="btn btn-sm btn-outline-primary" href="${plotUrl}" target="_blank">Abrir plot circular completo (${plotFileType.toUpperCase()})</a>
            </div>
        </div>
    ` : `
        <h6 class="mb-3">Distribuição de features anotadas</h6>
        <div class="viz-donut" style="background: conic-gradient(#0284c7 0 ${cdsPct}%, #f59e0b ${cdsPct}% ${cdsPct + trnaPct}%, #ef4444 ${cdsPct + trnaPct}% ${cdsPct + trnaPct + rrnaPct}%, #8b5cf6 ${cdsPct + trnaPct + rrnaPct}% 100%);">
            <div class="viz-donut-center">
                <div class="viz-donut-title">${formatNumber(total)}</div>
                <div class="viz-donut-sub">features</div>
            </div>
        </div>
        <div class="viz-legend mt-3">
            <span><i class="bi bi-square-fill" style="color:#0284c7"></i> CDS: ${formatNumber(cds)}</span>
            <span><i class="bi bi-square-fill" style="color:#f59e0b"></i> tRNA: ${formatNumber(trnas)}</span>
            <span><i class="bi bi-square-fill" style="color:#ef4444"></i> rRNA: ${formatNumber(rrnas)}</span>
            <span><i class="bi bi-square-fill" style="color:#8b5cf6"></i> ncRNA: ${formatNumber(ncrnas)}</span>
        </div>
    `;

    container.innerHTML = `
        <div class="viz-grid">
            <div class="viz-card">
                ${circularPlotHtml}
            </div>

            <div class="viz-card">
                <h6 class="mb-3">Resumo anotado do job ${jobData.job_id}</h6>
                <div class="viz-kpis">
                    <div><small>Tamanho do genoma</small><strong>${formatNumber(stats.genome_size || 0)} bp</strong></div>
                    <div><small>GC content</small><strong>${(stats.gc_content || 0).toFixed(2)}%</strong></div>
                    <div><small>Contigs</small><strong>${formatNumber(stats.n_contigs || 0)}</strong></div>
                    <div><small>N50</small><strong>${formatNumber(stats.n50 || 0)}</strong></div>
                    <div><small>Genes</small><strong>${formatNumber(genes)}</strong></div>
                    <div><small>Status</small><strong>${jobData.status || 'completed'}</strong></div>
                </div>

                ${plotFileType ? `
                    <p class="text-muted small mt-3 mb-0">Plot circular oficial gerado pelo Bakta.</p>
                ` : `
                    <p class="text-muted small mt-3 mb-0">Sem arquivo SVG/PNG neste job. Exibindo visualização de contingência por contagem.</p>
                `}
            </div>
        </div>
    `;
}
