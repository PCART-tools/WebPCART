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
                    <button
                        class="nav-button"
                        :class="{active: projectView === 'fixresult'}"
                        @click="projectView = 'fixresult'"
                    >FixResult</button>
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
                    <div v-if="!isUploading && project" class="current-project">
                        <div class="project-header">
                            <span class="project-path">{{project}}</span>
                            <button class="downloadProject" title="Download Project" @click="downloadProject">
                                <i class="fas fa-download"></i>
                            </button>
                        </div>
                        <div v-if="fileTree" class="file-tree">
                            <tree-view :tree-data="fileTree" :project-name="project"/>
                        </div>
                    </div>  
                </div>

                <div v-show="projectView === 'intermediate'" class="intermediate-content">
                    <b>Run fix command to get results</b>
                </div>

                <div v-show="projectView === 'fixresult'" class="result-content">
                    <b>Run fix command to get results</b>
                </div>
                
            </div>

            <div class="app-middle">
                <!-- 代码编辑栏 -->
                <div class="app-code">
                    <div class="editor-container" ref="editorRef" :class="{disabled: !currentFilePath}" v-show="currentFilePath"></div>
                    <div v-if="!currentFilePath" class="editor-placeholder">
                        <b>choose a file(.py / .txt) to edit</b>
                    </div>
                </div>
                
                <div class="app-terminal">
                    <b>Terminal</b>
                </div>
            </div>

            <!-- 配置栏 -->
            <div class="app-configuration">
                <b>Configuration</b>
                <!-- 环境配置栏 -->
                <div class="app-env">
                        <b>Import Virtual Environment</b>
                        <div class="env-section">
                            <button class="env-display-button" @click="openEnvDetailsModal('current')">
                                <b>currentEnv</b>
                            </button>
                            <button class="env-add-button" @click="openImportEnvModal('current')">import</button>
                        </div>
                        <div class="env-section">
                            <button class="env-display-button" @click="openEnvDetailsModal('target')">
                                <b>targetEnv</b>
                            </button>
                            <button class="env-add-button" @click="openImportEnvModal('target')">import</button>
                        </div>
                    </div>

                <!-- 修复库配置栏 -->
                <div class="app-target">
                    <b>Libraries to Fix</b>
                    <select class="target-select">
                        <option value="lib1">lib1</option>
                        <option value="lib2">lib2</option>
                        <option value="lib3">lib3</option>
                    </select>
                </div>

                <!-- 运行命令配置栏 -->
                <div class="app-command"> 
                    <b>Run Command</b>
                    <div class="command-container">
                        <input 
                            type="text"
                            class="command-input"
                            placeholder="Enter project run command"
                            v-model="runCommand"
                        />
                    </div>   
                </div>

                <button class="run-button">Run</button>     
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
                    <select class="form-control" disabled>
                        <option value="requirements">From requirements.txt</option>
                    </select>
                </div>

                <div class="form-group">
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

            <div v-if="isCreatingEnv" class="progress-section">
                <div class="progress-label">{{creatingEnvStep}}</div>
                <div class="progress-bar-background">
                    <div class="progress-bar-fill"
                     :style="{width: envCreationProgress + '%'}"></div>
                </div>
            </div>

            <div v-if="envCreationError" class="error-message">{{envCreationError}}</div>

            <div class="modal-footer">
                <button @click="closeImportEnvModal" class="cancel-button">Cancel</button>
                <button
                    @click="createEnvironment"
                    class="confirm-button"
                    :disabled="!requirementFile || isCreatingEnv">
                    {{isCreatingEnv? 'Creating...' : 'Confirm'}}
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
</template>

<script setup>
import {ref, onMounted, onUnmounted} from 'vue'
import * as monaco from 'monaco-editor'

// 导入拆分的模块
import TreeView from './components/TreeView.vue'
import { 
    project, 
    fileTree, 
    uploadProgress, 
    isUploading, 
    totalBatches, 
    currentBatch, 
    currentFilePath, 
    originalContent, 
    isContentModified,
    selectFolder,
    uploadFiles,
    saveFile,
    setProject,
    loadProjectTree,
    loadCurrentProject,
    downloadProject
} from './composables/projectManager'

import { 
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
    selectedEnvDetailsType,
    openImportEnvModal,
    closeImportEnvModal,
    handleRequirementSelect,
    createEnvironment,
    openEnvDetailsModal,
    closeEnvDetailsModal
} from './composables/envManager'

import { showNotification } from './composables/utils'

// ---项目栏功能---
// 项目视图状态
const projectView = ref('project')

// 编辑器相关
const editorRef = ref(null)
let editor = null
let handleKeyDown = null
const runCommand = ref('')

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
