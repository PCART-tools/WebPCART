<template>
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
</template>

<script setup>
import { ref } from 'vue'
import { showNotification } from '../composables/utils'
import { saveFile } from '../composables/projectManager'

// 从projectManager导入状态
import { currentFilePath, isContentModified } from '../composables/projectManager'

const props = defineProps(['node', 'projectName', 'basePath'])

const isExpanded = ref(false)

const toggleDirectory = () => {  // 展开或折叠文件夹
    isExpanded.value = !isExpanded.value;
}

const handleNodeClick = () => {  // 处理文件点击
    if(props.node.type === 'file'){
        // 允许的文件类型
        const allowedExtensions = ['.py', '.txt', 'md']

        // 检查文件类型
        const fileName = props.node.name.toLowerCase();
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

        loadFileContent();
    }else if(props.node.type === 'directory'){
        toggleDirectory();
    }
}

const getCurrentPath = () => {   // 获取当前节点路径
    if(props.basePath){
        return props.basePath + '/' + props.node.name;
    }
    return props.node.name;
}

const downloadItem = async () => {   // 下载文件
    try{
        const fullPath = getCurrentPath();

        const response = await fetch(`http://localhost:5000/project/download`, {
            method: 'POST',
            headers:{
                'Content-Type':'application/json'
            },
            body: JSON.stringify({
                projectName: props.projectName,
                path: fullPath,
                type: props.node.type
            })
        });

        if(response.ok){
            let filename = props.node.name;
            if(props.node.type !== 'file'){
                filename = `${props.node.name}.zip`;
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
}

const buildPath = (node) => {    // 构建文件路径
    const paths = [];
    let currentNode = node;

    while(currentNode){
        paths.unshift(currentNode.name);
        break;
    }

    return node.name;
}

const loadFileContent = async () => {    // 加载文件内容
    try{
        const fullPath = getCurrentPath();
        const response = await fetch('http://localhost:5000/project/load_file', {
            method: 'POST',
            headers:{
                'Content-Type':'application/json'
            },
            body: JSON.stringify({
                projectName: props.projectName,
                filePath: fullPath
            })
        });

        if(response.ok){
            const result = await response.json();
            if(result.status === 'success'){
                currentFilePath.value = fullPath;
                const originalContent = result.content;
                if(window.editor){
                    window.editor.setValue(result.content);
                    isContentModified.value = false;
                    window.editor.updateOptions({readOnly: false});
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
</script>