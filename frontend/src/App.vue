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
            <!-- 项目管理栏 -->
            <div class="app-project">
                <div class="project-title">
                    <b>Projects</b>
                    <button @click="selectFolder" title="import" class="import-button">
                        <i class="fas fa-plus"></i>
                    </button>
                </div>
                <div v-if="project" class="current-project">
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

            <div class="app-middle">
                <!-- 配置栏 -->
                <div class="app-config">
                    <div class="app-env">
                        <div class="env-section">
                            <button class="env-display-button"><b>currentEnv:</b></button>
                            <button class="env-add-button">import</button>
                        </div>
                        <div class="env-section">
                            <button class="env-display-button"><b>targetEnv:</b></button>
                            <button class="env-add-button">import</button>
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

                <!-- 代码编辑栏 -->
                <div class="app-code">
                    <div class="editor-container" ref="editorRef" :class="{disabled: !currentFilePath}"></div>
                    <div v-if="!currentFilePath" class="editor-placeholder">
                        choose a file(.py / .txt) to edit
                    </div>
                </div>
            </div>

            <!-- 运行结果栏 -->
            <div class="app-wrapper">
                <div class="resizer"></div>
                <div class="app-result">
                    <div class="result-tabs">
                        <button class="result-button"
                        :class="{'active':activeTab === 'terminal'}"
                        @click="activeTab = 'terminal'">
                            terminal
                        </button>
                        <button class="result-button"
                        :class="{'active':activeTab === 'intermediate'}"
                        @click="activeTab = 'intermediate'">
                            intermediate
                        </button>
                        <button class="result-button"
                        :class="{'active':activeTab === 'fixResult'}"
                        @click="activeTab = 'fixResult'">
                            fixResult
                        </button>
                    </div>
                    <div class="result-content"> 
                        <div v-if="activeTab === 'terminal'">terminal page</div>
                        <div v-if="activeTab === 'intermediate'">intermediate page</div>
                        <div v-if="activeTab === 'fixResult'">fixResult page</div>
                    </div>
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
                // 检查文件类型
                const fileName = this.node.name.toLowerCase();
                if(!fileName.endsWith('.py') && !fileName.endsWith('.txt')){
                    alert('Editing this type of file is not supported');
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
                    alert("Download Failed:" + error.message);
                }
            }catch(error){
                console.error('Download Failed:', error);
                alert('Download Failed:');
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
                        alert('Failed to load file' + result.message);
                    }
                }else{
                    alert('Failed to load file: ' + response.json());
                }
            }catch(error){
                console.error('Error loading file:', error);
                alert('Error loading file');
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

// 选择文件夹
const selectFolder = async() => {
    try{
        const input = document.createElement('input');
        input.type = 'file';
        input.webkitdirectory = true;
        input.directory = true;
        input.multiple = true;

        input.onchange = async(event) => {
            const files = event.target.files;
            
            if(files.length === 0){
                alert('Selected floder is empty');
                return;
            }

            // 获取文件夹名称
            const firstFile = files[0];
            let folderName = firstFile.webkitRelativePath.split('/')[0];
            await setProject(folderName);
            await uploadFiles(folderName, files);
        };

        input.click();
    }catch(error){
        console.error('Error selecting folder:', error);
        alert('Folder selection failed');
    }
}

// 上传本地文件到后端
const uploadFiles = async(projectName, files) => { 
    try{
        const formData = new FormData();
        formData.append('projectName', projectName);

        for(let i = 0; i < files.length; i++){
            formData.append('files', files[i]);
            formData.append(`paths[${i}]`, files[i].webkitRelativePath || files[i].name);
        }

        const response = await fetch('http://localhost:5000/project/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        if(result.status === 'success'){
            await loadProjectTree(projectName);
        }else{
            alert('Error uploading files: ' + result.message);
        }
    }catch(error){
        console.error('Error uploading files:', error);
        alert('Error uploading files');
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
            alert('file saved successfully');
        }else{
            alert('failed to save file' + result.message);
        }
    }catch(error){
        console.error('Error saving file:', error);
        alert('Error saving file');
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
            alert('Error adding project');
        }
    }catch(error){
        console.error('Error adding project:', error);
        alert('Error adding project');
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
            alert('Failed to load project tree' + result.message);
        }
    }catch(error){
        console.error('Error loading project Tree:', error);
        alert('Failed to load project tree');
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
        alert('Error loading project');
    }
}

const downloadProject = async() => {
    try{
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
            alert("Download Failed:" + error.message);
        }
    }catch(error){
        console.error('Download Failed:', error);
        alert('Download Failed:');
    }
}

const showInfo = (info) => {
    alert(info + ' button clicked');
}

// ---网页初始化---
const activeTab = ref('terminal')
const editorRef = ref(null)
let editor = null
let handleKeyDown = null

onMounted(() => { 
    // 创建编辑器实例
    if(editorRef.value){
        editor = monaco.editor.create(editorRef.value, {
            value: ' ',
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
    const resultBar = document.querySelector('.app-result');
    const appMain = document.querySelector('.app-main');
    const appMiddle = document.querySelector('.app-middle');

    const validWidth = appMain.offsetWidth - document.querySelector('.app-project').offsetWidth;
    let startX, startMiddleWidth, startResultWidth;

    const mouseDownHandler = function(e){
        startX = e.clientX;
        startMiddleWidth = appMiddle.offsetWidth;
        startResultWidth = resultBar.offsetWidth;

        document.addEventListener('mousemove', mouseMoveHandler)
        document.addEventListener('mouseup', mouseUpHandler)
        resizer.style.cursor = 'col-resize';
        document.body.style.cursor ='col-resize';
        e.preventDefault();
    };

    const mouseMoveHandler = function(e){ 
        const deltaX = e.clientX - startX;
        const newResultBarWidth = startResultWidth - deltaX;
        const newMiddleWidth = startMiddleWidth + deltaX;

        if(newResultBarWidth > 150 && newMiddleWidth > 600){
            resultBar.style.width = `${newResultBarWidth}px`;
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
    overflow-x: hidden;
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
    min-height: 100vh;
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
    width: 240px;
    border-right: 1px solid #e0e0e0;
    padding: 10px;
    position: relative;
}

.project-title{ 
    display: flex;
    justify-content: space-between;
    align-items: center;
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
    font-size: 14px;
}

.tree ul{
    list-style-type: none;
    padding-left: 20px;
}

.tree-node{
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 3px 0;
    cursor: pointer;
    user-select: none;
}

.tree-node:hover{
    background-color: #d2e0e7;
}

.download-button{
    margin-left: auto;
    background: none;
    border: none;
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.2s;
    padding: 2px 5px;
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
 }

 .env-add-button{
    flex: 1;
    padding: 10px 5px;
    border: 1px solid #ccc;
    border-radius: 5px;
    cursor: pointer;
    background: #50f9ffff;
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
}

.editor-container{
    flex: 1;
    border: 1px solid #e0e0e0;
    border-radius: 5px;
    overflow: hidden;
    height: calc(100vh - 200px);
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
.app-result{
    width: 300px;
    position: relative;
    flex: 1;
    overflow: auto;
}

.result-tabs{
    display: flex;
    border-bottom: 1px solid #e0e0e0;
}

.result-button{
    flex: 1;
    padding: 10px 0;
    border: none;
    border-right: 2px solid #474545ff;
    background: #f5f5f5;
    cursor: pointer;
    transition: all 0.3s;
}

.result-button.active{
    background: #fff;
    border-bottom: 2px solid #22fc00ff;
    font-weight: bold;
}

.result-content{
    flex: 1;
    padding: 10px;
    overflow: auto;
 }
</style>