import { computed, ref, reactive } from 'vue'
import { showNotification } from './utils'
import { resetFixState } from './fixManager'
import apiConfig from '../../config/apiconfig.js'

// 虚拟环境相关状态
const showImportModal = ref(false)
const importEnvMethod = ref('condapack')
const selectedEnvType = ref(null)

const pythonVersion = ref('python3.12')
const requirementFile = ref(null)

const condapackFile = ref(null)

const isCreatingCurrentEnv = ref(false)
const currentCreatingEnvStep = ref('Initializing')
const currentEnvCreationProgress = ref(0)
const currentEnvCreationError = ref('')
const currentEnv = ref({
    pythonVersion: '',
    dependencies: [],
    path: ''
})

const isCreatingTargetEnv = ref(false)
const targetCreatingEnvStep = ref('Initializing')
const targetEnvCreationProgress = ref(0)
const targetEnvCreationError = ref('')
const targetEnv = ref({
    pythonVersion: '',
    dependencies: [],
    path: ''
})

const configChanged = ref(true)

// 分片上传配置
const CHUNK_SIZE = 128 * 1024 * 1024
const UPLOAD_CONCURRENCY = 1;

// 打开导入环境窗口
export const openImportEnvModal = (envType) => {
    selectedEnvType.value = envType;
    showImportModal.value = true;
    requirementFile.value = null;
    condapackFile.value = null;
}

// 关闭导入环境窗口
export const closeImportEnvModal = () => {
    showImportModal.value = false;
    selectedEnvType.value = '';
}

// 处理文件选择
export const handleRequirementSelect = (e) => {
    const file = e.target.files[0];

    if(importEnvMethod.value === 'requirements'){
        if(file && file.name.toLowerCase().endsWith('.txt')){
            requirementFile.value = file;
        }else{
            showNotification('Please select a valid .txt file', 'warning');
            e.target.value = '';
        }
    }
}

export const handleCondapackSelect = (e) => {
    const file = e.target.files[0];

    if(importEnvMethod.value === 'condapack'){
        if(file && (file.name.toLowerCase().endsWith('.tar') || file.name.toLowerCase().endsWith('.tar.gz') || file.name.toLowerCase().endsWith('.tgz'))){
            condapackFile.value = file;
        }else{
            showNotification('Please select a valid conda pack file(.tar, .tar.gz, or .tgz)', 'warning');
            e.target.value = '';
        }
    }
}

// 初始化上传会话
async function initUploadSession(filename, fileSize, totalChunks, envType) {
    const url = `${apiConfig.BASE_URL}/venv/init_upload`;
    console.log('Initializing upload session:', { filename, fileSize, totalChunks, envType, url });
    
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
            filename,
            fileSize,
            totalChunks,
            envType
        })
    });
    
    if (!response.ok) {
        console.error('Failed to initialize upload session:', response.status, response.statusText);
        throw new Error(`Failed to initialize upload: ${response.statusText}`);
    }
    
    const result = await response.json();
    console.log('Upload session initialized successfully:', result);
    return result;
}

// 上传单个分片
async function uploadChunk(chunk, uploadSessionId, chunkIndex, totalChunks) {
    const url = `${apiConfig.BASE_URL}/venv/upload_chunk`;
    console.log('Uploading chunk:', { uploadSessionId, chunkIndex, totalChunks, url, chunkSize: chunk.size });
    
    const formData = new FormData();
    formData.append('chunk', chunk, `chunk_${chunkIndex}`);
    formData.append('uploadSessionId', uploadSessionId);
    formData.append('chunkIndex', chunkIndex.toString());
    formData.append('totalChunks', totalChunks.toString());
    
    const response = await fetch(url, {
        method: 'POST',
        credentials: 'include',
        body: formData
    });
    
    if (!response.ok) {
        console.error('Failed to upload chunk:', chunkIndex, response.status, response.statusText);
        throw new Error(`Chunk ${chunkIndex} upload failed: ${response.statusText}`);
    }
    
    const result = await response.json();
    console.log('Chunk uploaded successfully:', chunkIndex, result);
    return result;
}

// 取消上传会话
async function cancelUploadSession(uploadSessionId) {
    try {
        const url = `${apiConfig.BASE_URL}/venv/cancel_upload`;
        console.log('Cancelling upload session:', { uploadSessionId, url });
        
        await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ uploadSessionId })
        });
        console.log('Upload session cancelled successfully:', uploadSessionId);
    } catch (error) {
        console.error('Failed to cancel upload:', error);
    }
}

// 完成分片上传
async function completeUpload(uploadSessionId, envType, onProgress) {
    const url = `${apiConfig.BASE_URL}/venv/complete_upload`;
    console.log('Completing upload:', { uploadSessionId, envType, url });
    
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ uploadSessionId, envType })
    });
    
    if (!response.ok) {
        console.error('Failed to complete upload:', response.status, response.statusText);
        throw new Error(`Failed to complete upload: ${response.statusText}`);
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n\n');
        
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                try {
                    const data = JSON.parse(line.substring(6));
                    onProgress?.(data);
                } catch (e) {
                    console.error('Failed to parse SSE data:', e);
                }
            }
        }
    }
    console.log('Upload completion stream finished');
}

// 分片上传文件
async function uploadFileInChunks(file, envType, onProgress) {
    const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
    let uploadedChunks = 0;
    let uploadSessionId = null;
    
    try {
        // 初始化上传会话
        onProgress?.({ 
            progress: 0, 
            step: 'Initializing upload session',
            message: '准备上传...'
        });
        
        const initData = await initUploadSession(file.name, file.size, totalChunks, envType);
        uploadSessionId = initData.uploadSessionId;
        
        // 并行上传分片
        const uploadSingleChunk = async (chunkIndex) => {
            const start = chunkIndex * CHUNK_SIZE;
            const end = Math.min(start + CHUNK_SIZE, file.size);
            const chunk = file.slice(start, end);
            
            const result = await uploadChunk(chunk, uploadSessionId, chunkIndex, totalChunks);
            uploadedChunks++;
            
            const progress = (uploadedChunks / totalChunks) * 60; 
            const uploadedMB = (uploadedChunks * CHUNK_SIZE) / (1024 * 1024);
            const totalMB = file.size / (1024 * 1024);
            
            onProgress?.({
                progress: Math.min(progress, 60),
                step: `Uploading (${uploadedChunks}/${totalChunks})`,
                message: `上传中: ${uploadedMB.toFixed(1)}MB / ${totalMB.toFixed(1)}MB`
            });
            
            return result;
        };
        
        // 分批并行上传
        for (let i = 0; i < totalChunks; i += UPLOAD_CONCURRENCY) {
            const batchPromises = [];
            for (let j = 0; j < UPLOAD_CONCURRENCY && i + j < totalChunks; j++) {
                batchPromises.push(uploadSingleChunk(i + j));
            }
            await Promise.all(batchPromises);
        }
        
        onProgress?.({
            progress: 60,
            step: 'All chunks uploaded',
            message: '所有分片上传完成，准备合并...'
        });
        
        return uploadSessionId;
        
    } catch (error) {
        // 取消上传会话
        if (uploadSessionId) {
            await cancelUploadSession(uploadSessionId);
        }
        throw error;
    }
}

// 处理 SSE 流响应
function handleSSEStream(reader, decoder, envType, onSuccess, onError, onProgress) {
    return new Promise(async (resolve, reject) => {
        try {
            while(true){
                const {done, value} = await reader.read();
                if(done) break;

                const chunk = decoder.decode(value, {stream: true});
                const lines = chunk.split('\n');

                for(const line of lines){
                    if(line.startsWith('data: ')){
                        try{
                            const data = JSON.parse(line.substring(6));

                            if(data.status === 'progress'){
                                onProgress?.(data.step, data.progress);
                            }else if(data.status === 'error'){
                                const errorMsg = data.message.replace(/\u001b\[[0-9;]*m/g, '');
                                onError(errorMsg);
                                reject(new Error(errorMsg));
                                return;
                            }else if(data.status === 'success'){
                                onSuccess(data);
                                resolve(data);
                                return;
                            }
                            
                        }catch(e){
                            console.error('Error parsing JSON:', e);
                        }
                    }
                }
            }
        } catch (error) {
            reject(error);
        }
    });
}

// 使用 requirements.txt 创建环境
async function createEnvWithRequirements(envType, requirementsFile, pythonVersion, updateProgress, setError, setSuccess) {
    const formData = new FormData();
    formData.append('importEnvMethod', 'requirements');
    formData.append('envType', envType);
    formData.append('pythonVersion', pythonVersion);
    formData.append('requirements', requirementsFile);

    const response = await fetch('/venv/create', {
        method: 'POST',
        credentials: 'include',
        body: formData
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    await handleSSEStream(
        reader,
        decoder,
        envType,
        (data) => {
            setSuccess({
                pythonVersion: data.pythonVersion,
                dependencies: data.dependencies || [],
                path: data.path
            });
        },
        (errorMsg) => {
            setError(errorMsg);
        },
        (step, progress) => {
            updateProgress(step, progress);
        }
    );
}

// 使用 conda pack 创建环境
async function createEnvWithCondaPack(envType, condapackFile, updateProgress, setError, setSuccess) {
    // 分片上传
    const uploadSessionId = await uploadFileInChunks(
        condapackFile,
        envType,
        (progressData) => {
            updateProgress(progressData.step, progressData.progress);
        }
    );

    // 完成上传并处理
    const completeResponse = await fetch('/venv/complete_upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
            uploadSessionId,
            envType: envType
        })
    });

    if (!completeResponse.ok) {
        throw new Error(`Failed to complete upload: ${completeResponse.statusText}`);
    }

    const reader = completeResponse.body.getReader();
    const decoder = new TextDecoder();

    await handleSSEStream(
        reader,
        decoder,
        envType,
        (data) => {
            setSuccess({
                pythonVersion: data.pythonVersion,
                dependencies: data.dependencies || [],
                path: data.path
            });
        },
        (errorMsg) => {
            setError(errorMsg);
        },
        (step, progress) => {
            const adjustedProgress = 60 + (progress * 0.4);
            updateProgress(step, adjustedProgress);
        }
    );
}

// 创建虚拟环境
export const createEnvironment = async() => {
    if(importEnvMethod.value === 'requirements'){
        if(!requirementFile.value){
            showNotification('Please select a requirements.txt file', 'warning');
            return;
        }
    }else if(importEnvMethod.value === 'condapack'){
        if(!condapackFile.value){
            showNotification('Please select a conda pack file', 'warning');
            return;
        }
    }
    
    const isCurrent = selectedEnvType.value === 'current';
    
    // 设置初始状态
    if(isCurrent){
        currentEnv.value.path = '';
        isCreatingCurrentEnv.value = true;
        currentEnvCreationError.value = '';
        currentEnvCreationProgress.value = 0;
        currentCreatingEnvStep.value = 'Creating virtual environment';
    }else{
        targetEnv.value.path = '';
        isCreatingTargetEnv.value = true;
        targetEnvCreationError.value = '';
        targetEnvCreationProgress.value = 0;
        targetCreatingEnvStep.value = 'Creating virtual environment'; 
    }
    
    configChanged.value = true;
    resetFixState();

    // 定义状态更新函数
    const updateProgress = (step, progress) => {
        if(isCurrent){
            currentCreatingEnvStep.value = step;
            currentEnvCreationProgress.value = progress;
        }else{
            targetCreatingEnvStep.value = step;
            targetEnvCreationProgress.value = progress;
        }
    };

    const setError = (errorMsg) => {
        if(isCurrent){
            currentEnvCreationError.value = errorMsg;
            isCreatingCurrentEnv.value = false;
        }else{
            targetEnvCreationError.value = errorMsg;
            isCreatingTargetEnv.value = false;
        }
    };

    const setSuccess = (envData) => {
        if(isCurrent){
            currentEnvCreationProgress.value = 100;
            currentCreatingEnvStep.value = 'Environment created successfully';
            currentEnv.value = envData;

            setTimeout(() => {
                showNotification(`Current environment created successfully`, 'success');
                closeImportEnvModal();
            }, 1000);

            isCreatingCurrentEnv.value = false;
        }else{
            targetEnvCreationProgress.value = 100;
            targetCreatingEnvStep.value = 'Environment created successfully';
            targetEnv.value = envData;

            setTimeout(() => {
                showNotification(`Target environment created successfully`, 'success');
                closeImportEnvModal();
            }, 1000);

            isCreatingTargetEnv.value = false;
        }
    };

    try{
        if(importEnvMethod.value === 'requirements'){
            await createEnvWithRequirements(
                selectedEnvType.value,
                requirementFile.value,
                pythonVersion.value,
                updateProgress,
                setError,
                setSuccess
            );
        }else if(importEnvMethod.value === 'condapack'){
            await createEnvWithCondaPack(
                selectedEnvType.value,
                condapackFile.value,
                updateProgress,
                setError,
                setSuccess
            );
        }
    }catch(error){
        setError(error.message);
        console.error('Error creating environment:', error);
        showNotification(`Failed to create ${selectedEnvType.value} environment`);
    }
}

// 获取环境创建状态 
export const getCurrentEnvCreationStatus = () => ({
    isCreating: isCreatingCurrentEnv.value,
    step: currentCreatingEnvStep.value,
    progress: currentEnvCreationProgress.value,
    error: currentEnvCreationError.value
})

export const getTargetEnvCreationStatus = () => ({
    isCreating: isCreatingTargetEnv.value,
    step: targetCreatingEnvStep.value,
    progress: targetEnvCreationProgress.value,
    error: targetEnvCreationError.value
})

const showEnvDetailsModal = ref(false)
const envDetails = ref({})
const selectedEnvDetailsType = ref('')

// 打开环境详情窗口
export const openEnvDetailsModal = (envType) =>{
    selectedEnvDetailsType.value = envType;
    if(envType === 'current'){
        envDetails.value = currentEnv.value;
    }else{
        envDetails.value = targetEnv.value;
    }
    showEnvDetailsModal.value = true;
}

// 关闭环境详情窗口
export const closeEnvDetailsModal = () => {
    showEnvDetailsModal.value = false;
    selectedEnvDetailsType.value = '';
}

// 解析依赖
function parseDependency(dep){
    return dep.split('=')
}

// 获取版本升级的依赖库
const upgradLibraries = computed(() => {
    if(!currentEnv.value.dependencies || !targetEnv.value.dependencies){
        return []
    }

    // 解析环境依赖
    const currentDeps = new Map()
    currentEnv.value.dependencies.forEach(dep => {
        const [name, version] = dep.split('=')
        if(name && version){
            currentDeps.set(name.toLowerCase(), version)
        }
    })

    const targetDeps = new Map()
    targetEnv.value.dependencies.forEach(dep => {
        const [name, version] = dep.split('=')
        if(name && version){
            targetDeps.set(name.toLowerCase(), version)
        }
    })

    // 获取存在版本升级的依赖
    const upgradDeps = []
    
    for(const [name, targetVersion] of targetDeps){
        const currentVersion = currentDeps.get(name)
        if(currentVersion && compareVersions(targetVersion, currentVersion) > 0){
            upgradDeps.push({
                name,
                currentVersion,
                targetVersion
            })
        }
    }
    return upgradDeps
})

// 版本比较
function compareVersions(v1, v2){
    const arr1 = v1.split('.').map(Number);
    const arr2 = v2.split('.').map(Number);
    const maxLength = Math.max(arr1.length, arr2.length);

    for(let i = 0; i < maxLength; i++){
        // 缺失的位视为0
        const num1 = arr1[i] || 0;
        const num2 = arr2[i] || 0;

        if(num1 > num2) return 1;
        if(num1 < num2) return -1;
    }

    return 0;
}

const environmentsReady = computed(() => {
    return currentEnv.value.path && targetEnv.value.path
})

const runCommand = ref('')
const runFilePath = ref('')
const showCommandModal = ref(false)
const pythonFiles = ref([])
const selectedPythonFile = ref('')
const additionalArgs = ref('')

// 提取 Python 文件的函数
const extractPythonFiles = (treeNode, currentPath = '') => {
    let files = []
  
    if (treeNode.type === 'file' && treeNode.name.endsWith('.py')) {
        files.push(currentPath ? `${currentPath}/${treeNode.name}` : treeNode.name)
    } else if (treeNode.children) {
        const sortedChildren = [...treeNode.children].sort((a, b) => a.name.localeCompare(b.name));

        for (const child of sortedChildren) {
            const childPath = currentPath ? `${currentPath}/${treeNode.name}` : treeNode.name
            files = files.concat(extractPythonFiles(child, childPath))
        }
    }
  
    return files
}

// 更新项目时提取 Python 文件
const updatePythonFiles = (fileTree) => {
    if (fileTree) {
        pythonFiles.value = extractPythonFiles(fileTree, '')
    } else {
        pythonFiles.value = []
    }
}

// 打开命令导入窗口
const openCommandModal = (fileTree) => {
    if (fileTree) {
        updatePythonFiles(fileTree)
        showCommandModal.value = true
    }
}

// 关闭命令导入窗口
const closeCommandModal = () => {
    showCommandModal.value = false
}

// 保存命令
const saveCommand = (command, filePath) => {
    runCommand.value = command;
    runFilePath.value = filePath;
    configChanged.value = true;
    closeCommandModal();
}

// 导出相关状态
export {
    showImportModal,
    currentEnv,
    targetEnv,
    selectedEnvType,
    importEnvMethod,
    pythonVersion,
    requirementFile,
    condapackFile,
    isCreatingCurrentEnv,
    currentCreatingEnvStep,
    currentEnvCreationProgress,
    currentEnvCreationError,
    isCreatingTargetEnv,
    targetCreatingEnvStep,
    targetEnvCreationProgress,
    targetEnvCreationError,
    showEnvDetailsModal,
    envDetails,
    selectedEnvDetailsType,
    upgradLibraries,
    environmentsReady, 
    runCommand,
    runFilePath,
    showCommandModal,
    pythonFiles,
    selectedPythonFile,
    additionalArgs,
    configChanged,
    openCommandModal,
    closeCommandModal,
    saveCommand,
    updatePythonFiles
}