<template>
    <div class="app-container">
        <!-- 功能栏 -->
        <div class="function-bar">
            <b>WebPCART</b>
            <div class="function-buttons">
                <button @click="showInfo('setting')" title="setting">
                    <i class="fas fa-cog"></i>
                </button>
                <button @click="showInfo('help')" title="help">
                    <i class="fas fa-question-circle"></i>
                </button>
                <button @click="showInfo('about')" title="about">
                    <i class="fas fa-info-circle"></i>
                </button>
            </div>
        </div>

        <!-- 网页主体 -->
        <div class="app-main">
            <!-- 项目管理栏（含运行结果） -->
            <div class="app-project">
                <div class="project-nav">
                    <button
                        class="nav-button"
                        :class="{active: projectView === 'project'}"
                        @click="projectView = 'project'"
                    >Project</button>
                    <button
                        class="nav-button"
                        :class="{active: projectView === 'intermediate'}"
                        @click="projectView = 'intermediate'"
                    >Intermediate</button>
                </div>

                <div v-show="projectView === 'project'" class="project-content">
                    <div class="project-title">
                        <b>Projects</b>
                        <button @click="selectFolder" title="import" class="import-button">
                            <i class="fas fa-plus"></i>
                        </button>
                    </div>
                    <div v-if="isUploading" class="upload-progress-container">
                        <div class="progress-bar-background">
                            <div class="progress-bar-fill"
                                :style="{width: uploadProgress + '%'}"
                            ></div>
                        </div>
                        <div class="progress-percentage">{{ uploadProgress }} %</div>
                    </div>

                    <div v-if="!isUploading && project" class="project">
                        <div class="project-header">
                            <span class="project-path">{{project}}</span>
                            <button class="downloadProject" title="Download Project" @click="downloadProject">
                                <i class="fas fa-download"></i>
                            </button>
                        </div>
                        <div v-if="fileTree" class="file-tree">
                            <tree-view :tree-data="fileTree" :project-name="project" project-type="original"/>
                        </div> 
                    </div>  

                    <div v-if="!isUploading && fixedProject" class="project">
                        <div class="project-header">
                            <span class="project-path">{{project}} -fixed</span>
                            <button class="downloadProject" title="Download Project" @click="downloadProject('fixed')">
                                <i class="fas fa-download"></i>
                            </button>
                        </div>
                        <div v-if="fixedFileTree" class="file-tree">
                            <tree-view :tree-data="fixedFileTree" :project-name="fixedProject" project-type="fixed"/>
                        </div> 
                    </div> 
                </div>

                <div v-show="projectView === 'intermediate'" class="intermediate-content">
                    <b>Run fix command to get results</b>
                </div>               
            </div>

            <div class="app-code">
                <!-- 代码编辑栏 -->
                <div class="editor-container" ref="editorRef" :class="{disabled: !currentFilePath}" v-show="currentFilePath"></div>
                <div v-if="!currentFilePath" class="editor-placeholder">
                    <b>choose a file(.py / .txt) to edit</b>
                </div>
            </div>

            <!-- 配置栏 -->
            <div class="app-configuration">
                <b>Configuration</b>
                <!-- 环境配置栏 -->
                <div class="app-env">
                        <b>Import Virtual Environment</b>
                        <div class="env-section">
                            <button class="env-display-button" :class="{'env-ready': currentEnv.path}" @click="openEnvDetailsModal('current')">
                                <b>currentEnv</b>
                            </button>
                            <button class="env-add-button" @click="openImportEnvModal('current')">import</button>
                        </div>
                        <div class="env-section">
                            <button class="env-display-button" :class="{'env-ready': targetEnv.path}" @click="openEnvDetailsModal('target')">
                                <b>targetEnv</b>
                            </button>
                            <button class="env-add-button" @click="openImportEnvModal('target')">import</button>
                        </div>
                    </div>

                <!-- 修复库配置栏 -->
                <div class="app-target">
                    <b>Libraries to Fix</b>
                    <select class="target-select"
                            @change="handleLibrarySelect"
                            v-model="handleSelectedLibrary"
                            :disabled="!environmentsReady || upgradLibraries.length === 0">  
                        <option value="" disabled v-if="!environmentsReady">
                            Environment not ready
                        </option>

                        <option value="" disabled v-else-if="environmentsReady && upgradLibraries.length === 0">
                            No version changes
                        </option>

                        <option v-for="lib in upgradLibraries"
                                :key="lib.name"
                                :value="lib.name">{{ lib.name }}</option>
                    </select>

                    <div v-if="selectedLibrary" class="library-change-info">
                        <p>{{ getSelectedLibraryInfo() }}</p>
                    </div>
                </div>

                <!-- 运行命令配置栏 -->
                <div class="app-command"> 
                    <b>Run Command</b>
                    <div class="command-container">
                        <button
                            class="command-select-button"
                            @click="openCommandModal(fileTree)"
                            :disabled="!project"
                        >
                            {{ runCommand || 'Import run command...' }}
                        </button>
                    </div>   
                </div>

                <button class="run-button" 
                        :disabled="!project || !selectedLibrary || !runCommand"
                        @click="runFixCommand">
                    {{ isRunningFix ? 'Running...' : 'Run' }}
                </button>    
                
                <div v-if="isRunningFix" class="fix-progress-container">
                    <div class="progress-label">
                        {{ fixProgressStep }}
                    </div>
                    <div class="progress-bar-background">
                        <div class="progress-bar-fill"
                         :style="{width: fixProgress + '%'}"></div>
                    </div>
                    <div class="progress-percentage">{{ fixProgress }}%</div>
                </div>

                <div v-if="fixError" class="error-message">
                    {{ fixError }}
                </div>
            </div>
        </div>
    </div>

    <!-- 环境导入窗口 -->
    <div v-if="showImportModal" class="modal-overlay" @click="closeImportEnvModal">
        <div class="modal-container" @click.stop>
            <div class="modal-header">
                <h3>Import {{selectedEnvType}} Environment</h3>
                <button class="modal-close" @click="closeImportEnvModal">&times;</button>
            </div>

            <div class="modal-body"> 
                <div class="form-group">
                    <label>Import Method:</label>
                    <select v-model="importEnvMethod" class="form-control">
                        <option value="requirements">From requirements.txt</option>
                        <option value="condapack">From condapack</option>
                    </select>
                </div>

                <div v-if="importEnvMethod === 'requirements'" class="import-method-section">
                    <div>
                        <label>Python Version</label>
                        <select v-model="pythonVersion" class="form-control">
                            <option value="python3.8">Python 3.8</option>
                            <option value="python3.9">Python 3.9</option>
                            <option value="python3.10">Python 3.10</option>
                            <option value="python3.11">Python 3.11</option>
                            <option value="python3.12">Python 3.12</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label>Requirements File</label>
                        <input type="file" accept=".txt" @change="handleRequirementSelect" class="file-input"/>
                    </div>
                </div>

                <div v-else-if="importEnvMethod == 'condapack'" class="import-method-section">
                    <div class="form-group">
                        <label>Conda Pack File</label>
                        <input type="file" accept=".tar,.tar.gz,.tgz" @change="handleCondapackSelect" class="file-input"/>
                    </div>
                </div>
            </div>

            <div v-if="selectedEnvType == 'current' ? isCreatingCurrentEnv : isCreatingTargetEnv" class="progress-section">
                <div class="progress-label">
                    {{selectedEnvType == 'current'? currentCreatingEnvStep : targetCreatingEnvStep}}
                </div>
                <div class="progress-bar-background">
                    <div class="progress-bar-fill"
                     :style="{width: (selectedEnvType == 'current' ? currentEnvCreationProgress : targetEnvCreationProgress) + '%'}"></div>
                </div>
            </div>

            <div v-if="selectedEnvType == 'current' ? currentEnvCreationError : targetEnvCreationError" class="error-message">
                {{selectedEnvType === 'current' ? currentEnvCreationError : targetEnvCreationError}}
            </div>

            <div class="modal-footer">
                <button @click="closeImportEnvModal" class="cancel-button">Cancel</button>
                <button
                    @click="createEnvironment"
                    class="confirm-button"
                    :disabled="(importEnvMethod === 'requirements' && !requirementFile) ||
                                (importEnvMethod === 'condapack' && !condapackFile) ||  
                                (selectedEnvType === 'current' ? isCreatingCurrentEnv : isCreatingTargetEnv)">
                    {{(selectedEnvType === 'current' ? isCreatingCurrentEnv : isCreatingTargetEnv) ? 'Creating...' : 'Confirm'}}
                </button>
            </div>
        </div>
    </div>
    <!-- 虚拟环境详情窗口 -->
    <div v-if="showEnvDetailsModal" class="modal-overlay" @click="closeEnvDetailsModal">
        <div class="modal-container" @click.stop>
            <div class="modal-header">
                <h3>{{selectedEnvDetailsType}} Environment Details</h3>
                <button class="modal-close" @click="closeEnvDetailsModal">&times;</button>
            </div>

            <div class="modal-body">
                <div class="form-group">
                    <label>Python Version</label>
                    <div class="env-detail-value">{{envDetails.pythonVersion}}</div>
                </div>

                <div class="form-group">
                    <label>Dependencies:</label>
                    <div v-if="envDetails.dependencies && envDetails.dependencies.length > 0" class="dependencies-list">
                        <div v-for="(dep, index) in envDetails.dependencies" :key="index" class="dependency-item">
                            {{dep}}
                        </div>
                    </div>
                </div>

                <div class="modal-footer">
                    <button @click="closeEnvDetailsModal" class="cancel-button">Close</button>
                </div>
            </div>
        </div>
    </div>

    <CommandSelectionModal
        :show-command-modal="showCommandModal"
        :project="fileTree"
        :python-files="pythonFiles"
        :selected-python-file="selectedPythonFile"
        :additional-args="additionalArgs"
        @closeCommandModal="closeCommandModal"
        @saveCommand="saveCommand"
    />
</template>

<script setup>
import {ref, onMounted, onUnmounted, computed} from 'vue'
import * as monaco from 'monaco-editor'

// 导入拆分的模块
import TreeView from './components/TreeView.vue'
import { 
    project, 
    fileTree, 
    fixedProject,
    fixedFileTree,
    uploadProgress, 
    isUploading, 
    currentFilePath, 
    originalContent, 
    isContentModified,
    selectFolder,
    saveFile,
    loadCurrentProject,
    downloadProject,
    setFixedProject,
} from './composables/projectManager'

import { 
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
    openImportEnvModal,
    closeImportEnvModal,
    handleRequirementSelect,
    handleCondapackSelect,
    createEnvironment,
    openEnvDetailsModal,
    closeEnvDetailsModal,
    upgradLibraries,
    environmentsReady,
    runCommand,
    runFilePath,
    showCommandModal,
    pythonFiles,
    selectedPythonFile,
    additionalArgs,
    openCommandModal,
    closeCommandModal,
    saveCommand,
} from './composables/configManager'

import CommandSelectionModal from './components/RunCommandModal.vue';

import { showNotification } from './composables/utils'

// 项目视图状态
const projectView = ref('project')

// 编辑器相关
const editorRef = ref(null)
let editor = null
let handleKeyDown = null

// 修复库相关
const selectedLibrary = ref(null)

// 修复进度相关
const isRunningFix = ref(false)
const fixProgressStep = ref('Initializing')
const fixProgress = ref(0)
const fixError = ref('')


const handleSelectedLibrary = computed({
    get(){
        return selectedLibrary.value ? selectedLibrary.value.name : ''
    },
    set(value){
        const selectedLib = upgradLibraries.value.find(l => l.name === value)

        if(selectedLib){
            selectedLibrary.value = {
                name: selectedLib.name,
                currentVersion: selectedLib.currentVersion,
                targetVersion: selectedLib.targetVersion
            };
    }else{
        selectedLibrary.value = null;
    }
    }
})

const getSelectedLibraryInfo = () =>{
    if(selectedLibrary.value){
        return `${selectedLibrary.value.name}: ${selectedLibrary.value.currentVersion} -> ${selectedLibrary.value.targetVersion}`
    }
    return ''
}

// 运行修复命令
const runFixCommand = async() => {
    const configData = {
        projectName: project.value,
        libName: selectedLibrary.value.name,
        currentVersion: selectedLibrary.value.currentVersion,
        targetVersion: selectedLibrary.value.targetVersion,
        runCommand: runCommand.value,
        runFilePath: runFilePath.value
    }

    isRunningFix.value = true;
    fixError.value = '';
    fixProgress.value = 0;
    fixProgressStep.value = 'Starting fix process';

    try{
        const response = await fetch('http://localhost:5000/fix/run_fix',{
            method:'POST',
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
                        } else if (data.status === 'error') {
                            fixError.value = data.message.replace(/\u001b\[[0-9;]*m/g, '');  // 去除ANSI控制字符
                            isRunningFix.value = false;
                            showNotification(`Fix failed: ${data.message}`, 'error');
                            return;
                        } else if (data.status === 'success') {
                            fixProgress.value = 100;
                            fixProgressStep.value = data.message;

                            await setFixedProject(project.value)

                            setTimeout(() => {
                                showNotification('Fix completed successfully', 'success');
                            }, 1000);

                            isRunningFix.value = false;
                            return;
                        }
                    } catch (e) {
                        console.error('Error parsing fix progress JSON:', e);
                    }
                }
            }
        }
    }catch(error){
        fixError.value = error.message;
        isRunningFix.value = false;
        console.error('Failed to run fix with progress', error);
        showNotification('Failed to run fix:' + error.message, 'error');
    }
}

onMounted(() => { 
    // 创建编辑器实例
    if(editorRef.value){
        window.editor = monaco.editor.create(editorRef.value, {
            value: '',
            language: 'python',
            scrollBeyondLastLine: false,
            fontSize: 14,
            lineNumbers: 'on',
            folding: true,
            lineDecorationsWidth: 'on',
            lineNumbersMinChars: 3,
            wordWrap: 'on',
            contextmenu: true,
            automaticLayout: true,
            readOnly: true,
            fontFamily: 'ui-monospace, "Cascadia Code", "Source Code Pro", Menlo, Consolas, "DejaVu Sans Mono", monospace'
        })

        window.editor.onDidChangeModelContent(() => {
            const currentContent = window.editor.getValue();
            isContentModified.value = (currentContent !== originalContent.value);
        })
    }

    // 实现ctrl+s保存
    handleKeyDown = (e) => {
        if(e.ctrlKey && e.key === 's'){
            e.preventDefault();
            if(currentFilePath.value && isContentModified.value){
                saveFile();
            }
        }
    }

    document.addEventListener('keydown', handleKeyDown);

    loadCurrentProject();
})

onUnmounted(() => {
    if(window.editor){
        window.editor.dispose();
        window.editor = null;
    }

    document.removeEventListener('keydown', handleKeyDown);
})
</script>

<style lang="scss">
@use "./styles/_base.scss";
@use "./styles/_layout.scss";
@use "./styles/_project.scss";
@use "./styles/_config.scss";
@use "./styles/_editor.scss";
@use "./styles/_modal.scss";
</style>
