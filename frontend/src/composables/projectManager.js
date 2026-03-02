import { ref, reactive } from 'vue'
import { showNotification } from './utils'
import { runCommand } from './configManager'

// 项目管理相关状态
const project = ref(null)
const fileTree = ref(null)

const fixCompleted = ref(false)
const instrumentProject = ref(null)
const instrumentFileTree = ref(null)

const currentProjectType = ref('original')
const uploadProgress = ref(0)
const isUploading = ref(false)
const totalBatches = ref(0)
const currentBatch = ref(0)
const currentFilePath = ref(null)
const originalContent = ref('')
const isContentModified = ref(false)

// 选中文件状态
export const selectedFile = reactive({
    path: '',
    projectType: ''
})

export function updateSelectedFile(path, projectType){
    selectedFile.path = path;
    selectedFile.projectType = projectType;
}

// 选择文件夹
export const selectFolder = async() => {
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
            
            runCommand.value = null;
            fixCompleted.value = false;
            clearinstrumentProject();
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
export const uploadFiles = async(projectName, files) => { 
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
export const saveFile = async(projectType = 'original') => {
    try{
        const currentContent = window.editor.getValue();

        const response = await fetch('http://localhost:5000/project/save_file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                projectName: project.value,
                filePath: currentFilePath.value,
                content: currentContent,
                projectType: projectType
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
export const setProject = async(path) => {
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
export const loadProjectTree = async(projectName, type = 'original') => {
    try{
        const response = await fetch('http://localhost:5000/project/tree', {
            method: 'POST',
            headers:{
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({name: projectName, type: type})
        });

        const result = await response.json();
        if(result.status === 'success'){
            if(type == 'original'){
                fileTree.value = result.tree;
            }else if(type == 'instrument'){
                instrumentFileTree.value = result.tree;
            }
            
            if(!currentFilePath.value && window.editor){
                window.editor.updateOptions({readOnly: true});
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
export const loadCurrentProject = async() => {
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

export const downloadProject = async(projectType = 'original') => {
    try{
        // 检查是否有未保存的修改
        if(isContentModified.value && currentFilePath.value){
            const save = confirm('There are unsaved changes. Do you want to save them before downloading?');
            if(save){
                await saveFile(projectType);
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
                type: 'project',
                projectType: projectType
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

// 设置修复后的项目
export const setCopyProject = async(path) => {
    try{
        instrumentProject.value = path;
        await loadProjectTree(path, 'instrument');
    }catch(error){
        console.error('Error setting instrument project:', error);
        showNotification('Failed to set instrument project', 'error');
    }
}

// 清空修复后的项目数据
export const clearinstrumentProject = () => {
    instrumentProject.value = null;
    instrumentFileTree.value = null;
}

// 导出相关状态
export {
    project,
    fileTree,
    instrumentProject,
    instrumentFileTree,
    uploadProgress,
    isUploading,
    totalBatches,
    currentBatch,
    currentFilePath,
    originalContent,
    isContentModified,
    currentProjectType,
    fixCompleted
}