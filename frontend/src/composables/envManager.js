import { ref } from 'vue'
import { showNotification } from './utils'

// TODO：新增使用packages导入环境的方法
// 虚拟环境相关状态
const showImportModal = ref(false)
const importEnvMethod = ref('requirements')
const selectedEnvType = ref(null)
const pythonVersion = ref('python3.12')
const requirementFile = ref(null)

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

// 打开导入环境窗口
export const openImportEnvModal = (envType) => {
    selectedEnvType.value = envType;
    showImportModal.value = true;
    requirementFile.value = null;
}

// 关闭导入环境窗口
export const closeImportEnvModal = () => {
    showImportModal.value = false;
    selectedEnvType.value = '';
}

// 选择文件
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

// TODO: 当前环境和目标环境不能同时进行导入
// 创建虚拟环境
export const createEnvironment = async() => {
    if(importEnvMethod.value == 'requirements'){
        if(!requirementFile.value){
            showNotification('Please select a requirements file', 'warning');
            return;
        }

        if(selectedEnvType.value === 'current'){
            isCreatingCurrentEnv.value = true;
            currentEnvCreationError.value = '';
            currentEnvCreationProgress.value = 0;
            currentCreatingEnvStep.value = 'Creating virtual environment'
        }else{
            isCreatingTargetEnv.value = true;
            targetEnvCreationError.value = '';
            targetEnvCreationProgress.value = 0;
            targetCreatingEnvStep.value = 'Creating virtual environment' 
        }
        

        try{
            const formData = new FormData();
            formData.append('importEnvMethod', 'requirements');
            formData.append('envType', selectedEnvType.value);
            formData.append('pythonVersion', pythonVersion.value);
            formData.append('requirements', requirementFile.value);

            const response = await fetch('http://localhost:5000/venv/create', {
                method: 'POST',
                body: formData
            })

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            // 持续获取创建进度
            while(true){
                const {done, value} = await reader.read();
                if(done) break;

                const chunk = decoder.decode(value, {stream: true});
                const lines = chunk.split('\n');

                for(const line of lines){
                    if(line.startsWith('data: ')){
                        try{
                            const data = JSON.parse(line.substring(6));

                            if(data.type == 'current'){
                                if(data.status === 'progress'){
                                    currentCreatingEnvStep.value = data.step;
                                    currentEnvCreationProgress.value = data.progress;
                                }else if(data.status === 'error'){
                                    currentEnvCreationError.value = data.message.replace(/\u001b\[[0-9;]*m/g, '');  // 去除ANSI控制字符
                                    isCreatingCurrentEnv.value = false;
                                    return;
                                }else if(data.status === 'success'){
                                    currentEnvCreationProgress.value = 100;
                                    currentCreatingEnvStep.value = 'Environment created successfully';

                                    currentEnv.value = {
                                        pythonVersion: data.pythonVersion,
                                        dependencies: data.dependencies || [],
                                        path: data.path
                                    };

                                    setTimeout(() => {
                                        showNotification(`Current environment created successfully`, 'success')
                                        closeImportEnvModal();
                                    }, 1000);

                                    isCreatingCurrentEnv.value = false;
                                    return;
                                }
                            }else{
                                if(data.status === 'progress'){
                                    targetCreatingEnvStep.value = data.step;
                                    targetEnvCreationProgress.value = data.progress;
                                }else if(data.status === 'error'){
                                    targetEnvCreationError.value = data.message.replace(/\u001b\[[0-9;]*m/g, '');  // 去除ANSI控制字符
                                    isCreatingTargetEnv.value = false;
                                    return;
                                }else if(data.status === 'success'){
                                    targetEnvCreationProgress.value = 100;
                                    targetCreatingEnvStep.value = 'Environment created successfully';

                                    targetEnv.value = {
                                        pythonVersion: data.pythonVersion,
                                        dependencies: data.dependencies || [],
                                        path: data.path
                                    };

                                    setTimeout(() => {
                                        showNotification(`Target environment created successfully`, 'success')
                                        closeImportEnvModal();
                                    }, 1000);

                                    isCreatingTargetEnv.value = false;
                                    return;
                                }                                
                            }
                            
                        }catch(e){
                            console.error('Error parsing JSON:', e);
                        }
                    }
                }
            }
        }catch(error){
            if(selectedEnvType.value == 'current'){
                currentEnvCreationError.value = error.message;
                isCreatingCurrentEnv.value = false;
            }else{
                targetEnvCreationError.value = error.message;
                isCreatingTargetEnv.value = false;
            }

            console.error('Error creating environment:', error);
            showNotification(`Failed to create ${selectedEnvType.value} environment: `, 'error');
        }
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

export const openEnvDetailsModal = (envType) =>{
    selectedEnvDetailsType.value = envType;
    if(envType === 'current'){
        envDetails.value = currentEnv.value;
    }else{
        envDetails.value = targetEnv.value;
    }
    showEnvDetailsModal.value = true;
}

export const closeEnvDetailsModal = () => {
    showEnvDetailsModal.value = false;
    selectedEnvDetailsType.value = '';
}

// 导出相关状态
export {
    showImportModal,
    importEnvMethod,
    selectedEnvType,
    pythonVersion,
    requirementFile,
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
    selectedEnvDetailsType
}