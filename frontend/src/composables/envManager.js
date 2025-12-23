import { ref } from 'vue'
import { showNotification } from './utils'

// 虚拟环境相关状态
const showImportModal = ref(false)
const importEnvMethod = ref('requirements')
const selectedEnvType = ref(null)
const pythonVersion = ref('python3.12')
const requirementFile = ref(null)
const isCreatingEnv = ref(false)
const creatingEnvStep = ref('Initializing')
const envCreationProgress = ref(0)
const envCreationError = ref('')

const currentEnv = ref({
    pythonVersion: '',
    dependencies: [],
    path: ''
})
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

// 创建虚拟环境
export const createEnvironment = async() => {
    if(importEnvMethod.value == 'requirements'){
        if(!requirementFile.value){
            showNotification('Please select a requirements file', 'warning');
            return;
        }

        isCreatingEnv.value = true;
        envCreationError.value = '';
        envCreationProgress.value = 0;
        creatingEnvStep.value = 'Creating virtual environment'

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

                            if(data.status === 'progress'){
                                creatingEnvStep.value = data.step;
                                envCreationProgress.value = data.progress;
                            }else if(data.status === 'error'){
                                envCreationError.value = data.message.replace(/\u001b\[[0-9;]*m/g, '');  // 去除ANSI控制字符
                                isCreatingEnv.value = false;
                                return;
                            }else if(data.status === 'success'){
                                envCreationProgress.value = 100;
                                creatingEnvStep.value = 'Environment created successfully';

                                if(selectedEnvType.value === 'current'){
                                    currentEnv.value = {
                                        pythonVersion: pythonVersion.value,
                                        dependencies: data.dependencies || [],
                                        path: data.path
                                    };
                                }else{
                                    targetEnv.value = {
                                        pythonVersion: pythonVersion.value,
                                        dependencies: data.dependencies || [],
                                        path: data.path
                                    };
                                }

                                setTimeout(() => {
                                    showNotification(`${selectedEnvType.value} environment created successfully`, 'success')
                                    closeImportEnvModal();
                                }, 1000);

                                isCreatingEnv.value = false;
                                return;
                            }
                        }catch(e){
                            console.error('Error parsing JSON:', e);
                        }
                    }
                }
            }
        }catch(error){
            envCreationError.value = error.message
            console.error('Error creating environment:', error);
            showNotification(`Failed to create ${selectedEnvType.value} environment: `, 'error');
            isCreatingEnv.value = false;
        }
    }
}

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
    envCreationProgress.value = 0;
    envCreationError.value = '';
    creatingEnvStep.value = 'Initializing';
}

// 导出相关状态
export {
    showImportModal,
    importEnvMethod,
    selectedEnvType,
    pythonVersion,
    requirementFile,
    isCreatingEnv,
    creatingEnvStep,
    envCreationProgress,
    envCreationError,
    currentEnv,
    targetEnv,
    showEnvDetailsModal,
    envDetails,
    selectedEnvDetailsType
}