import { ref } from 'vue'
import { project, loadProjectTree, fixCompleted, setInstrumentProject } from './projectManager'
import { configChanged, runCommand, runFilePath } from './configManager'
import { showNotification } from './utils'

// 修复库相关状态
const selectedLibrary = ref(null)

// 修复进度相关状态
const isRunningFix = ref(false)
const fixProgressStep = ref('Initializing')
const fixProgress = ref(0)
const fixLog = ref('')

// 获取选中的库信息
export const getSelectedLibraryInfo = () =>{
    if(selectedLibrary.value){
        return `${selectedLibrary.value.name}: ${selectedLibrary.value.currentVersion} -> ${selectedLibrary.value.targetVersion}`
    }
    return ''
}

// 设置选中的库
export const setSelectedLibrary = (library) => {
    selectedLibrary.value = library;
}

// 运行修复命令
export const runFixCommand = async() => {
    if (!project.value || !selectedLibrary.value || !runCommand.value) {
        showNotification('Missing required parameters for fix command', 'error');
        return;
    }

    const configData = {
        projectName: project.value,
        libName: selectedLibrary.value.name,
        currentVersion: selectedLibrary.value.currentVersion,
        targetVersion: selectedLibrary.value.targetVersion,
        runCommand: runCommand.value,
        runFilePath: runFilePath.value,
        fixCompleted: fixCompleted.value
    }

    isRunningFix.value = true;
    fixLog.value = '';
    fixProgress.value = 0;
    fixProgressStep.value = 'Starting fix process';

    try{
        const response = await fetch('/fix/run_fix',{
            method:'POST',
            credentials: 'include',
            'headers':{
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(configData)
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        // 持续获取修复进度
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.substring(6));

                        if (data.status === 'progress') {
                            fixProgressStep.value = data.step;
                            fixProgress.value = data.progress;
                            fixLog.value += `${data.step}\n`
                        } else if (data.status === 'error') {
                            const errorMessage = data.message.replace(/\u001b\[[0-9;]*m/g, '');  // 去除ANSI控制字符
                            fixLog.value += `ERROR: ${errorMessage}\n`;
                            isRunningFix.value = false;
                            return;
                        } else if (data.status === 'success') {
                            fixProgress.value = 100;
                            fixProgressStep.value = data.message;
                            fixLog.value += `${data.message}\n`;

                            await setInstrumentProject(project.value)
                            await loadProjectTree(project.value)

                            setTimeout(() => {
                                showNotification('Fix completed successfully', 'success');
                            }, 1000);

                            configChanged.value = false;
                            fixCompleted.value = true;
                            isRunningFix.value = false;
                            return;
                        }else if (data.status === 'log') {
                            if (data.content) {
                                const logLines = data.content.split('\n');
                                logLines.forEach(logLine => {
                                    if (logLine.trim()) {
                                        fixLog.value += logLine + '\n';
                                    }
                                });
                            }
                        }
                    } catch (e) {
                        console.error('Error parsing fix progress JSON:', e);
                    }
                }
            }
        }
    }catch(error){
        fixLog.value += `[${fixLog.value.split('\n').length - 1}] ERROR: ${error.message}\n`;
        isRunningFix.value = false;
        console.error('Failed to run fix with progress', error);
        showNotification('Failed to run fix:' + error.message, 'error');
    }
}

// 重置修复状态
export const resetFixState = () => {
    selectedLibrary.value = null
    isRunningFix.value = false
    fixProgressStep.value = 'Initializing'
    fixProgress.value = 0
    fixLog.value = ''
}

export {
    selectedLibrary,
    isRunningFix,
    fixProgressStep,
    fixProgress,
    fixLog
}