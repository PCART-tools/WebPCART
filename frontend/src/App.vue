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
                        :class="{active: projectView === 'detail'}"
                        @click="projectView = 'detail'"
                    >Details</button>
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

                    <!-- <div v-if="!isUploading && fixedProject" class="divider-line"></div>

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
                    </div>  -->
                </div>

                <div v-show="projectView === 'detail'" class="detail-content">
                    <div v-if="fixCompleted" class="detail-buttons">
                        <button @click="getReport" class="detail-button">Report</button>
                    </div>
                    
                    <div v-else>
                        <b>Run fix command to get results</b>
                    </div>       
                </div>               
            </div>

            <div class="app-code">
                <!-- 代码编辑栏 -->
                <div v-show="projectView === 'project' && currentFilePath" class="editor-container" ref="editorRef" :class="{disabled: !currentFilePath}"></div>
                <div v-show="projectView === 'project' && !currentFilePath" class="editor-placeholder">
                    <b>choose a file(.py / .txt) to edit</b>
                </div>

                <!-- 结果展示栏 -->
                <div v-show="projectView === 'detail'" class="detail-view-container">
                    <div v-if="reportData" class="report-content">
                        <div class="report-header">
                            <h3>Compatibility Report</h3>
                        </div>
                        
                        <!-- 统计信息卡片 -->
                        <div class="report-stats" v-if="reportData.stat_info">
                            <div class="run-command-section">
                                <h4>Run Command: <span class="command-text">{{ reportData.stat_info.run_command }}</span></h4>
                            </div>
                            
                            <div class="stats-grid first-row">
                                <div class="stat-card">
                                    <h4>Total Files</h4>
                                    <p class="stat-number">{{ reportData.stat_info.total_file_number || 0 }}</p>
                                </div>
                                <div class="stat-card">
                                    <h4>Total APIs</h4>
                                    <p class="stat-number">{{ reportData.stat_info.total_api_number || 0 }}</p>
                                </div>
                            </div>
                            
                            <div class="stats-grid second-row">
                                <div class="stat-card">
                                    <h4>Covered APIs</h4>
                                    <p class="stat-number">{{ reportData.stat_info.covered_number || 0 }}</p>
                                </div>
                                <div class="stat-card">
                                    <h4>Uncovered APIs</h4>
                                    <p class="stat-number">{{ (reportData.stat_info.not_covered_number) || 0 }}</p>
                                </div>
                            </div>
                            
                            <div class="stats-grid third-row">
                                <div class="stat-card">
                                    <h4>Compatible APIs</h4>
                                    <p class="stat-number">{{ reportData.stat_info.compatible_number || 0 }}</p>
                                </div>
                                <div class="stat-card">
                                    <h4>Unknown Compatible APIs</h4>
                                    <p class="stat-number">{{ reportData.stat_info.unknown_compatible_number || 0 }}</p>
                                </div>
                                <div class="stat-card">
                                    <h4>Incompatible APIs</h4>
                                    <p class="stat-number">{{ reportData.stat_info.incompatible_number || 0 }}</p>
                                </div>
                            </div>
                            
                            <div class="stats-grid fourth-row">
                                <div class="stat-card">
                                    <h4>Successfully Repaired</h4>
                                    <p class="stat-number">{{ reportData.stat_info.successfully_repaired_number || 0 }}</p>
                                </div>
                                <div class="stat-card">
                                    <h4>Failed to Repair</h4>
                                    <p class="stat-number">{{ reportData.stat_info.failed_repair_number || 0 }}</p>
                                </div>
                                <div class="stat-card">
                                    <h4>Unknown Repair Status</h4>
                                    <p class="stat-number">{{ reportData.stat_info.unknown_repair_status_number || 0 }}</p>
                                </div>
                            </div>
                        </div>
                        
                        <!-- API详细信息 -->
                        <div class="api-details" v-if="reportData.api_details && reportData.api_details.length > 0">
                            <h4>Detailed API Analysis</h4>
                            <div class="api-table-container">
                                <table class="api-table">
                                    <thead>
                                        <tr>
                                            <th>API Call</th>
                                            <th>Location</th>
                                            <th>Coverage</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr v-for="(api, index) in reportData.api_details" :key="index" :class="getRowClass(api)" @click="showAPIDetail(api)">
                                            <td><code>{{ api.invoked_api }}</code></td>
                                            <td>{{ api.location }}</td>
                                            <td>
                                                <span :class="api.coverage === 'Yes' ? 'coverage-covered' : 'coverage-not-covered'">
                                                    {{ api.coverage }}
                                                </span>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        
                        <div v-else-if="reportData">
                            <p>No API details available in the reportData.</p>
                        </div>
                    </div>
                    <div v-else class="detail-placeholder">
                        <b>Select a command to view details</b>
                    </div>
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
                        @click="runFixCommand()">
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
    <EnvironmentImportModal
        :show-import-modal="showImportModal"
        :selected-env-type="selectedEnvType"
        :import-env-method="importEnvMethod"
        :python-version="pythonVersion"
        :requirement-file="requirementFile"
        :condapack-file="condapackFile"
        :is-creating-current-env="isCreatingCurrentEnv"
        :current-creating-env-step="currentCreatingEnvStep"
        :current-env-creation-progress="currentEnvCreationProgress"
        :current-env-creation-error="currentEnvCreationError"
        :is-creating-target-env="isCreatingTargetEnv"
        :target-creating-env-step="targetCreatingEnvStep"
        :target-env-creation-progress="targetEnvCreationProgress"
        :target-env-creation-error="targetEnvCreationError"
        @close-import-env-modal="closeImportEnvModal"
        @handle-requirement-select="handleRequirementSelect"
        @handle-condapack-select="handleCondapackSelect"
        @create-environment="createEnvironment"
    />

    <!-- 虚拟环境详情窗口 -->
    <EnvironmentDetailsModal
        :show-env-details-modal="showEnvDetailsModal"
        :env-details="envDetails"
        :selected-env-details-type="selectedEnvDetailsType"
        @close-env-details-modal="closeEnvDetailsModal"
    />

    <CommandSelectionModal
        :show-command-modal="showCommandModal"
        :project="fileTree"
        :python-files="pythonFiles"
        :selected-python-file="selectedPythonFile"
        :additional-args="additionalArgs"
        @closeCommandModal="closeCommandModal"
        @saveCommand="saveCommand"
    />

    <APIDetailModal 
    :show="showAPIDetailModal" 
    :api-detail="selectedAPIDetail" 
    @close="closeAPIDetailModal"
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
    uploadProgress, 
    isUploading, 
    currentFilePath, 
    originalContent, 
    isContentModified,
    selectFolder,
    saveFile,
    downloadProject,
    currentProjectType,
    fixCompleted
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
    showCommandModal,
    pythonFiles,
    selectedPythonFile,
    additionalArgs,
    openCommandModal,
    closeCommandModal,
    saveCommand,
} from './composables/configManager'

import { 
    reportData,
    getReport,
    showAPIDetailModal,
    closeAPIDetailModal,
    showAPIDetail,
    selectedAPIDetail
} from './composables/detailManager'

import {
    selectedLibrary,
    isRunningFix,
    fixProgressStep,
    fixProgress,
    fixError,
    getSelectedLibraryInfo,
    runFixCommand
} from './composables/fixManager'

import CommandSelectionModal from './components/RunCommandModal.vue';
import APIDetailModal from './components/APIDetailModal.vue';
import EnvironmentImportModal from './components/EnvironmentImportModal.vue';
import EnvironmentDetailsModal from './components/EnvironmentDetailsModal.vue';
import { showNotification } from './composables/utils';

// 项目视图状态
const projectView = ref('project')

// 编辑器相关
const editorRef = ref(null)
let editor = null
let handleKeyDown = null

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

const getRowClass = (api) => {
  if (api.coverage === 'No' || api.coverage === 'no' || api.coverage === false) {
    return 'uncovered-row';
  } else if (api.compatible) {
    return 'covered-compatible-row';
  } else {
    return 'covered-incompatible-row';
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
                saveFile(currentProjectType.value);
            }
        }
    }

    document.addEventListener('keydown', handleKeyDown);
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
@use "./styles/_detail.scss";
</style>
