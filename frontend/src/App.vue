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
                <!-- 配置栏 -->
                <div class="app-config">
                    <div class="app-env">
                        <div class="env-section">
                            <button class="env-display-button" @click="openEnvDetailsModal('current')">
                                <b>currentEnv:</b>
                                <span v-if="currentEnv.pythonVersion">{{currentEnv.pythonVersion}}</span>
                            </button>
                            <button class="env-add-button" @click="openImportEnvModal('current')">import</button>
                        </div>
                        <div class="env-section">
                            <button class="env-display-button" @click="openEnvDetailsModal('target')">
                                <b>targetEnv:</b>
                                <span v-if="currentEnv.pythonVersion">{{targetEnv.pythonVersion}}</span>
                            </button>
                            <button class="env-add-button" @click="openImportEnvModal('target')">import</button>
                        </div>
                    </div>
                    <div class="app-target">
                        <b>Libraries to Fix</b>
                        <select class="target-select">
                            <option value="lib1">lib1</option>
                            <option value="lib2">lib2</option>
                            <option value="lib3">lib3</option>
                        </select>
                        <button class="run-button">Run</button>
                    </div>
                </div>

                <!-- 运行命令栏 -->
                <div class="app-command"> 
                    <div class="command-container">
                        <input 
                            type="text"
                            class="command-input"
                            placeholder="Please enter the project run command"
                            v-model="runCommand"
                        />
                    </div>   
                </div>

                <!-- 代码编辑栏 -->
                <div class="app-code">
                    <div class="editor-container" ref="editorRef" :class="{disabled: !currentFilePath}" v-show="currentFilePath"></div>
                    <div v-if="!currentFilePath" class="editor-placeholder">
                        <b>choose a file(.py / .txt) to edit</b>
                    </div>
                </div>
            </div>

            <!-- 终端栏 -->
            <div class="app-wrapper">
                <div class="resizer"></div>
                <div class="app-terminal">
                    <b>Terminal</b>
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

// ---项目栏功能---
// 文件节点视图
const currentFilePath = ref(null)
const originalContent = ref('')
const isContentModified = ref(false)

const TreeNode = {
    name: 'TreeNode',
    props: ['node', 'projectName', 'basePath'],
    template: ` 
        <li>
            <div class="tree-node" @click="handleNodeClick">
                <i v-if="node.type === 'directory'"
                    @click.stop="toggleDirectory"
                    class="folder-toggle"
                    :class="isExpanded ? 'fa fa-chevron-down' : 'fa fa-chevron-right'">
                </i>
                <i v-if="node.type === 'directory'"
                    class= "fas fa-file folder-icon"
                ></i>
                <i v-else
                    class= "fas fa-file file-icon"
                ></i>
                <span>{{node.name}}</span> 
                <button @click.stop="downloadItem(node)" class="download-button" title="Download">
                    <i class="fas fa-download"></i>
                </button>
            </div>
            <ul v-if="node.type === 'directory' && node.children && node.children.length && isExpanded">
                <tree-node 
                    v-for="(child, index) in node.children"
                    :key="index"
                    :node="child"
                    :project-name="projectName"
                    :base-path="getCurrentPath()"
                />
            </ul>
        </li>
    `,
    data(){
        return{
            isExpanded: false
        }
    },
    methods:{
        toggleDirectory(){  // 展开或折叠文件夹
            this.isExpanded = !this.isExpanded;
        },
        handleNodeClick(){  // 处理文件点击
            if(this.node.type === 'file'){
                // 允许的文件类型
                const allowedExtensions = ['.py', '.txt', 'md']

                // 检查文件类型
                const fileName = this.node.name.toLowerCase();
                const isAllowed = allowedExtensions.some(ext => fileName.endsWith(ext))

                if(!isAllowed){
                    showNotification('Editing this type of file is not supported', 'warning');
                    return;
                }

                // 检查是否需要保存上一份文件
                if(isContentModified.value){
                    const saveChanges = confirm('The current file has unsaved changes. Do you want to save them?');
                    if(saveChanges){
                        saveFile();
                    }
                }

                this.loadFileContent();
            }else if(this.node.type === 'directory'){
                this.toggleDirectory();
            }
        },
        getCurrentPath(){   // 获取当前节点路径
            if(this.basePath){
                return this.basePath + '/' + this.node.name;
            }
            return this.node.name;
        },
        async downloadItem(){   // 下载文件
            try{
                const fullPath = this.getCurrentPath();

                const response = await fetch(`http://localhost:5000/project/download`, {
                    method: 'POST',
                    headers:{
                        'Content-Type':'application/json'
                    },
                    body: JSON.stringify({
                        projectName: this.projectName,
                        path: fullPath,
                        type: this.node.type
                    })
                });

                if(response.ok){
                    let filename = this.node.name;
                    if(this.node.type !== 'file'){
                        filename = `${this.node.name}.zip`;
                    }

                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');

                    a.href = url;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                }else{
                    const error = await response.json();
                    showNotification("Failed to download:" + error.message, 'error');
                }
            }catch(error){
                console.error('Failed to download:', error);
                 showNotification("Failed to download:" + error.message, 'error');
            }
        },
        buildPath(node){    // 构建文件路径
            const paths = [];
            let currentNode = node;

            while(currentNode){
                paths.unshift(currentNode.name);
                break;
            }

            return node.name;
        },
        async loadFileContent(){    // 加载文件内容
            try{
                const fullPath = this.getCurrentPath();
                const response = await fetch('http://localhost:5000/project/load_file', {
                    method: 'POST',
                    headers:{
                        'Content-Type':'application/json'
                    },
                    body: JSON.stringify({
                        projectName: this.projectName,
                        filePath: fullPath
                    })
                });

                if(response.ok){
                    const result = await response.json();
                    if(result.status === 'success'){
                        currentFilePath.value = fullPath;
                        originalContent.value = result.content;
                        if(editor){
                            editor.setValue(result.content);
                            isContentModified.value = false;
                            editor.updateOptions({readOnly: false});
                        }
                    }else{
                        showNotification('Failed to load file' + result.messagem , 'error');
                    }
                }else{
                    showNotification('Failed to load file: ' + response.json(), 'error');
                }
            }catch(error){
                console.error('Failed to load file:', error);
                showNotification("Failed to load file:" + error.message, 'error');
            }
        }
    }
}

// 文件树视图
const TreeView = {
    name: 'TreeView',
    props: ['treeData', 'projectName'],
    components:{
        TreeNode
    },
    template: `
        <ul class="tree">
            <tree-node 
                v-for="(node, index) in treeData.children"
                :key="index"
                :node="node"
                :project-name="projectName"
                :base-path="''"
            />
        </ul>
    `
}

const project = ref(null)
const fileTree = ref(null)
const uploadProgress = ref(0)
const isUploading = ref(false)
const totalBatches = ref(0)
const currentBatch = ref(0)

// 选择文件夹
const selectFolder = async() => {
    try{
        if(project.value){
            const shouldContinue = confirm('The current project will be lost. Are you sure you want to import a new project?');
            if(!shouldContinue){
                return;
            }
        }

        const input = document.createElement('input');
        input.type = 'file';
        input.webkitdirectory = true;
        input.directory = true;
        input.multiple = true;

        input.onchange = async(event) => {
            const files = event.target.files;

            // 获取文件夹名称
            const firstFile = files[0];
            let folderName = firstFile.webkitRelativePath.split('/')[0];
            await setProject(folderName);
            await uploadFiles(folderName, files);
        };

        input.click();
    }catch(error){
        console.error('Failed to select folder:', error);
        showNotification('Failed to select folder', 'error');
    }
}

// 上传本地文件到后端
const uploadFiles = async(projectName, files) => { 
    isUploading.value = true;
    uploadProgress.value = 0;

    const BATCH_SIZE = 50; // 每批次上传文件数
    try{
        const batches = [];
        totalBatches.value = Math.ceil(files.length / BATCH_SIZE);
        currentBatch.value = 0;

        // 重置代码编辑器
        currentFilePath.value = null;
        originalContent.value = '';
        if(editor){
            editor.setValue('');
            editor.updateOptions({readOnly: true});
        }

        // 分割文件
        for(let i = 0; i < files.length; i += BATCH_SIZE){
            batches.push(Array.from(files).slice(i, i + BATCH_SIZE))
        }

        // 分批上传文件
        for(let batchIndex = 0; batchIndex < batches.length; batchIndex++){
            const formData = new FormData();
            const batch = batches[batchIndex];
            
            formData.append('projectName', projectName);
            formData.append('batchIndex', batchIndex);
            
            for(let i = 0; i < batch.length; i++){
                formData.append('files', batch[i]);
                const relativePath = batch[i].webkitRelativePath || batch[i].name;
                formData.append(`paths[${i}]`, relativePath);
            }

            const response = await fetch('http://localhost:5000/project/upload_batch', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            if(result.status === 'success'){
                currentBatch.value = batchIndex + 1;
                uploadProgress.value = Math.round(((batchIndex + 1) / batches.length) * 100);
            }else{
                throw new Error('Failed to upload files: ' + result.message);
            }

            await new Promise(resolve => setTimeout(resolve, 100))
        }

        showNotification(`${files.length} files Uploaded completed`, 'success');
        await loadProjectTree(projectName);
    }catch(error){
        console.error('Failed to upload files:', error);
        showNotification('Failed to upload files', 'error');
    }finally{
        setTimeout(() => {
            isUploading.value = false;
            uploadProgress.value = 0;
            totalBatches.value = 0;
            currentBatch.value = 0;
        }, 500)
    }
}

// 保存已修改文件
const saveFile = async() => {
    try{
        const currentContent = editor.getValue();

        const response = await fetch('http://localhost:5000/project/save_file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                projectName: project.value,
                filePath: currentFilePath.value,
                content: currentContent
            })
        });

        const result = await response.json();
        if(result.status === 'success'){
            originalContent.value = currentContent;
            isContentModified.value = false;
            showNotification('File saved successfully', 'success');
        }else{
            showNotification('Failed to save file', 'error');
        }
    }catch(error){
        console.error('Error saving file:', error);
        showNotification('Failed to save file', 'error');
    }
}

// 添加项目到后端
const setProject = async(path) => {
    try{
        const response = await fetch('http://localhost:5000/project', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({path})
        });

        const result = await response.json();
        if(result.status === 'success'){
            project.value = result.path;
        }else{
            showNotification('Failed to add project', 'error');
        }
    }catch(error){
        console.error('Error adding project:', error);
        showNotification('Failed to add project', 'error');
    }
}

// 加载项目树
const loadProjectTree = async(projectName) => {
    try{
        const response = await fetch('http://localhost:5000/project/tree', {
            method: 'POST',
            headers:{
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({name: projectName})
        });

        const result = await response.json();
        if(result.status === 'success'){
            fileTree.value = result.tree;
            if(!currentFilePath.value && editor){
                editor.updateOptions({readOnly: true});
            }
        }else{
            showNotification('Failed to load project', 'error');
        }
    }catch(error){
        console.error('Error loading project Tree:', error);
        showNotification('Failed to load project', 'error');
    }
}

// 加载当前项目
const loadCurrentProject = async() => {
    try{
        const response = await fetch('http://localhost:5000/project');
        const result = await response.json();
        if(result.status === 'success' && result.project){
            project.value = result.project;
            await loadProjectTree(result.project);
        }
    }catch(error){
        console.error('Error loading project:', error);
        showNotification('Failed to load project', 'error');
    }
}

const downloadProject = async() => {
    try{
        // 检查是否有未保存的修改
        if(isContentModified.value && currentFilePath.value){
            const save = confirm('There are unsaved changes. Do you want to save them before downloading?');
            if(save){
                await saveFile();
            }
        }

        const response = await fetch(`http://localhost:5000/project/download`, {
            method: 'POST',
            headers:{
                'Content-Type':'application/json'
            },
            body: JSON.stringify({
                projectName: project.value,
                path: '.',
                type: 'project'
            })
        });

        if(response.ok){
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');

            a.href = url;
            a.download = project.value + '.zip';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        }else{
            const error = await response.json();
            showNotification('Failed to download', 'error');
        }
    }catch(error){
        console.error('Download Failed:', error);
        showNotification('Failed to download', 'error');
    }
}

// ---虚拟环境相关功能---
const showImportModal = ref(false)
const importEnvMethod = ref('requirements')
const selectedEnvType = ref(null)
const pythonVersion = ref('python3.9')
const requirementFile = ref(null)
const isCreatingEnv = ref(false)

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
const openImportEnvModal = (envType) => {
    selectedEnvType.value = envType;
    showImportModal.value = true;
    requirementFile.value = null;
}

// 关闭导入环境窗口
const closeImportEnvModal = () => {
    showImportModal.value = false;
    selectedEnvType.value = '';
}

// 选择文件
const handleRequirementSelect = (e) => {
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
const createEnvironment = async() => {
    if(importEnvMethod.value == 'requirements'){
        if(!requirementFile.value){
            showNotification('Please select a requirements file', 'warning');
            return;
        }

        isCreatingEnv.value = true;
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

            const result = await response.json();
            if(result.status === 'success'){
                if(selectedEnvType.value === 'current'){
                    currentEnv.value = {
                        pythonVersion: pythonVersion.value,
                        dependencies: result.dependencies || [],
                        path: result.path
                    };
                }else{
                    targetEnv.value = {
                        pythonVersion: pythonVersion.value,
                        dependencies: result.dependencies || [],
                        path: result.path
                    };
                }

                showNotification(`${selectedEnvType.value} environment created successfully`, 'success');
                closeImportEnvModal();
            }else{
                showNotification(`Failed to create ${selectedEnvType.value} environment: `, 'error');
            }
        }catch(error){
            console.error('Error creating environment:', error);
            showNotification(`Failed to create ${selectedEnvType.value} environment: `, 'error');
        }finally{
            isCreatingEnv.value = false;
        }
    }
}

const showEnvDetailsModal = ref(false)
const envDetails = ref({})
const selectedEnvDetailsType = ref('')

const openEnvDetailsModal = (envType) =>{
    selectedEnvDetailsType.value = envType;
    if(envType === 'current'){
        envDetails.value = currentEnv.value;
    }else{
        envDetails.value = targetEnv.value;
    }
    showEnvDetailsModal.value = true;
}

const closeEnvDetailsModal = () => {
    showEnvDetailsModal.value = false;
    selectedEnvDetailsType.value = '';
}

// ---通用函数---
// 消息弹窗功能
const showNotification = (message, type) => {
    const notification = document.createElement('div');
    notification.textContent = message;

    notification.style.position = 'fixed';
    notification.style.left = '50%';
    notification.style.top = '20px';
    notification.style.borderRadius = '5px';
    notification.style.color = 'white';
    notification.style.zIndex = '9999';
    notification.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.2)'
    notification.style.transition = 'all 0.3s ease'
    notification.style.opacity = '0'
    notification.style.transform = 'translateX(-50%)'
    notification.style.fontSize = '20px'

    if(type === 'success'){
        notification.style.backgroundColor = '#4CAF50'
    }else if(type === 'warning'){
        notification.style.backgroundColor = '#FFC107'
    }else{
        notification.style.backgroundColor = '#F44336'
    }
    

    document.body.appendChild(notification);

    setTimeout(() =>{
        notification.style.opacity = '1';
        notification.style.transform = 'translateY(0)';
    }, 10);

    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(20px)';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 2000);
}

// ---网页初始化---
const projectView = ref('project')
const editorRef = ref(null)
let editor = null
let handleKeyDown = null
const runCommand = ref('')

onMounted(() => { 
    // 创建编辑器实例
    if(editorRef.value){
        editor = monaco.editor.create(editorRef.value, {
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

        editor.onDidChangeModelContent(() => {
            const currentContent = editor.getValue();
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

    // 实现拉伸功能
    const resizer = document.querySelector('.resizer');
    const terminalBar = document.querySelector('.app-terminal');
    const appMain = document.querySelector('.app-main');
    const appMiddle = document.querySelector('.app-middle');

    const validWidth = appMain.offsetWidth - document.querySelector('.app-project').offsetWidth;
    let startX, startMiddleWidth, startTerminalWidth;

    const mouseDownHandler = function(e){
        startX = e.clientX;
        startMiddleWidth = appMiddle.offsetWidth;
        startTerminalWidth = terminalBar.offsetWidth;

        document.addEventListener('mousemove', mouseMoveHandler)
        document.addEventListener('mouseup', mouseUpHandler)
        resizer.style.cursor = 'col-resize';
        document.body.style.cursor ='col-resize';
        e.preventDefault();
    };

    const mouseMoveHandler = function(e){ 
        const deltaX = e.clientX - startX;
        const newTerminalBarWidth = startTerminalWidth - deltaX;
        const newMiddleWidth = startMiddleWidth + deltaX;

        if(newTerminalBarWidth > 150 && newMiddleWidth > 600){
            terminalBar.style.width = `${newTerminalBarWidth}px`;
            appMiddle.style.width = `${newMiddleWidth}px`;
            if(editor){
                editor.layout();
            }
        }
    }

    const mouseUpHandler = function(){
        resizer.style.cursor = '';
        document.body.style.cursor = '';
        document.removeEventListener('mousemove', mouseMoveHandler)
        document.removeEventListener('mouseup', mouseUpHandler)
    }

    resizer.addEventListener('mousedown', mouseDownHandler);

    loadCurrentProject();
})

onUnmounted(() => {
    if(editor){
        editor.dispose();
        editor = null;
    }

    document.removeEventListener('keydown', handleKeyDown);
})
</script>

<style>
@import url("https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css");

/* 全局样式 */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-size: 15px;
}

.app-container{ 
    width: 100vw;
    height: 100vh;
    display: flex;
    flex-direction: column;
    padding-top: 60px;
    overflow: hidden;
}

/* 功能栏 */
.function-bar{
    height: 60px;
    border-bottom: 1px solid #e0e0e0;
    background: #f9f8f8ff;
    padding-left: 10px;
    font-weight: bold;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-right: 10px;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 100;
}

.function-buttons button{
    margin-left: 10px;
    border: none;
    background: none;
    padding: 5px 10px;
    cursor:pointer;
    font-size: 20px;
}

.app-main{
    display: flex;
    min-height: calc(100vh - 60px);
    width: 100%;

}

/* 项目拉伸 */
.app-wrapper{
    display: flex;
    min-width: 200px;
}

.resizer{ 
    width: 5px;
    cursor: col-resize;
    background-color: #ccc;
}

.resizer:hover{
    background-color: #999;
    cursor: col-resize;
}

/* 项目管理栏 */
.app-project{
    width: 270px;
    border-right: 1px solid #e0e0e0;
    padding: 10px;
    position: relative;
    display: flex;
    flex-direction: column;
    height: 100%;
}

.project-nav{
    display: flex;
    margin-bottom: 10px;
    border-bottom: 1px solid #e0e0e0;
    gap: 3px;
}

.nav-button{
    flex: 1;
    padding: 8px 0;
    background: #f0f0f0;
    cursor: pointer;
    font-size: 15px;
    border: 2px solid #474545ff;
    border-radius: 5px;
}

.nav-button.active{
    background: #fff;
    border-bottom: 2px solid #22fc00ff;
    font-weight: bold;
}

/* 项目页 */
.project-content{
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    height: 100%;
}

.project-title{ 
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.upload-progress-container{
    margin-top: 15px;
    padding: 10px;
    background-color: #e3f2fd;
    border-radius: 5px;
    border: 1px solid #e0e0e0;
}

.progress-bar-background{
    width: 100%;
    height: 12px;
    background-color: #e0e0e0;
    border-radius: 5px;
    overflow: hidden;
    margin-bottom: 5px;
}

.progress-bar-fill{
    height: 100%;
    background: linear-gradient(to right, #4CAF50, #8BC34A);
}

.progress-percentage{
    font-size: 12px;
    text-align: center;
    color: #666;
}

.project-title .import-button{
    border: none;
    background: none;
    padding: 5px 10px;
    cursor: pointer;
    font-size: 20px;
}

.current-project{
    margin-top: 15px;
    display: flex;
    flex-direction: column;
    flex: 1;
    overflow: hidden;
}

.project-header{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px;
    background-color: #f0f0f0;
    border-radius: 5px;
}

.downloadProject{
    margin-left: auto;
    background: none;
    border: none;
}

.folder-toggle{
    margin-right: 5px;
    cursor: pointer;
    width: 12px;
    text-align: center;
}

.folder-icon{
    color: #FFA500
}

.file-icon{
    color: #888;
}

.file-tree{
    margin-top: 15px;
    font-size: 8px;
    flex: 1;
    overflow-y: auto;
    overflow-x: auto;
}

.tree ul{
    list-style-type: none;
    padding-left: 20px;
    min-width: 100%;
    display: block;
}

.tree-node{
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 1px 0;
    width: fit-content;
    min-width: 100%;
    cursor: pointer;
    user-select: none;
}

.tree-node:hover{
    background-color: #d2e0e7;
}

.tree-node span{
    white-space: nowrap;
    flex: 1;
    min-width: 10px;
}

.download-button{
    margin-left: auto;
    background: none;
    border: none;
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.2s;
    padding: 2px 5px;
    flex-shrink: 0;
}

.tree-node:hover .download-button{
    opacity: 1;
}

.download-button:hover{
    background-color: #e0e0e0;
    border-radius: 3px;
}

/* 中心部分 */
.app-middle{
    flex: 1;
    display: flex;
    flex-direction: column;
    border-right: 1px solid #e0e0e0;
}

/* 虚拟环境配置栏 */
.app-config{
    height: 130px;
    padding: 10px;
    border-bottom: 1px solid #e0e0e0;
    position: relative;
    display: flex;
}

.app-env{
    flex: 3;
    padding-right: 10px;
    border-right: 1px solid #e0e0e0;
    display: flex;
    flex-direction: column;
    height: 100%;
    gap: 10px;
}

.env-section{
    flex: 1;
    display: flex;
    gap: 10px;
    align-items: center;
}

.env-display-button{
    flex: 5;
    padding: 10px 5px;
    border: 1px solid #ccc;
    border-radius: 5px;
    cursor: pointer;
    background: #fff;
    text-align: left;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
 }

 .env-add-button{
    flex: 1;
    padding: 10px 5px;
    border: 1px solid #ccc;
    border-radius: 5px;
    cursor: pointer;
    background: #50f9ffff;
 }

 /* 运行命令栏 */
 .app-command{
    height: 60px;
    padding: 10px;
    border-bottom: 1px solid #e0e0e0;
    display: flex;
    align-items: center;
 }

 .command-container{
    width: 100%
 }

 .command-input{ 
    width: 100%;
    padding: 10px 15px;
    border: 1px solid #ccc;
    font-size: 16px;
    outline: none;
 }

 .command-input:focus{
    border-color: #50f9ffff;
    box-shadow: 0 0 2px rgba(80, 249, 255, 0.2);
 }

 .command-input::placeholder{
    color: #999;
 }

 /* 项目目标配置栏 */
.app-target{
    flex: 1;
    padding: 0 10px;
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.target-select{
    padding: 8px 5px;
    border: 1px solid #ccc;
    border-radius: 5px;
    width: 100%;
}

.run-button{ 
    padding: 6px 5px;
    border: 1px solid #ccc;
    border-radius: 5px;
    cursor: pointer;
    background: #22fc00ff;
    color: white;
    width: 30%;
    margin: 0 auto;
}

/* 代码编辑栏 */
.app-code{
    flex: 1;
    padding: 10px;
    display: flex;
    flex-direction: column;
    position: relative;
}

.editor-container{
    flex: 1;
    border: 1px solid #e0e0e0;
    border-radius: 5px;
    overflow: hidden;
    height: 100%;
}

.editor-placeholder{
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: #888;
}

.editor-container.disabled{
    opacity: 0.5;
    pointer-events: none;
}

/* 终端栏 */
.app-terminal{
    width: 300px;
    position: relative;
    flex: 1;
    overflow: auto;
}

/* 窗口样式 */
.modal-overlay{
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.modal-container{
    background-color: white;
    border-radius: 10px;
    width: 500px;
    max-width: 90%;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    display: flex;
    flex-direction: column;
    max-height: 90vh;
}

.modal-header{
    padding: 20px;
    border-bottom: 1px solid #eee;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.modal-header h3{
    margin: 0;
    font-size: 18px;
}

.modal-close{
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
    color: #999;
}

.modal-close:hover{
    color: #333;
}

.modal-body{
    padding: 20px;
    flex: 1;
    overflow-y: auto;
}

.form-group{
    margin-bottom: 20px;
}

.form-group label{
    display: block;
    margin-bottom: 8px;
    font-weight: bold;
}

.form-control{
    width: 100%;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 5px;
    font-size: 14px;
}

.form-control:disabled{
    background-color: #f0f0f0;
    color: #999;
}

.modal-footer{
    padding: 15px 20px;
    border-top: 1px solid #eee;
    display: flex;
    justify-content: flex-end;
    gap: 10px;
}

.cancel-button
.confirm-button{
    padding: 10px 20px;
    border-radius: 5px;
    cursor: pointer;
    font-size: 14px;
}

.file-input{
    width: 100%;
    padding: 10px 0;
}

.file-name{
    margin-top: 8px;
    font-size: 14px;
    color: #666;
}

.env-detail-value{
    padding: 10px;
    background-color: #f5f5f5;
    border-radius: 5px;
    border: 1px solid #ddd;
    min-height: 20px;
}

.dependencies-list{
    max-height: 200px;
    overflow-y: auto;
    border: 1px solid #ddd;
    border-radius: 5px;
    padding: 10px;
}

.dependency-item{
    padding: 5px 0;
}
</style>