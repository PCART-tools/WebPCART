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
                <div class="app-project-title">
                    <b>Projects</b>
                    <button @click="showInfo('import')" title="import" class="import-button">
                        <i class="fas fa-plus"></i>
                    </button>
                </div>
            </div>

            <div class="app-middle">
                <!-- 配置栏 -->
                <div class="app-config">
                    <div class="app-env">
                        <div class="env-section">
                            <button class="env-display-button">currentEnv</button>
                            <button class="env-add-button">import</button>
                        </div>
                        <div class="env-section">
                            <button class="env-display-button">targetEnv</button>
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
                    <div class="editor-container" ref="editorRef"></div>
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

const activeTab = ref('terminal')
const codeContent = ref(`# 输入代码`)
const editorRef = ref(null)
let editor = null

const showInfo = (info) => {
    alert(info + ' button clicked');
}

onMounted(() => { 
    // 创建编辑器实例
    if(editorRef.value){
        editor = monaco.editor.create(editorRef.value, {
            value: codeContent.value,
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
        })

        editor.onDidChangeModelContent(() => {
            codeContent.value = editor.getValue();
        })
    }

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
})

onUnmounted(() => {
    if(editor){
        editor.dispose();
        editor = null;
    }
})
</script>

<style>
@import url("https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css");

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

.app-container{ 
    width: 100vw;
    height: 100vh;
    display: flex;
    flex-direction: column;
    padding-top: 60px;
    overflow-x: hidden;
}

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

.app-project{
    width: 240px;
    border-right: 1px solid #e0e0e0;
    padding: 10px;
    position: relative;
}

.app-project-title{ 
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.app-project-title .import-button{
    border: none;
    background: none;
    padding: 5px 10px;
    cursor: pointer;
    font-size: 20px;
}

.app-middle{
    flex: 1;
    display: flex;
    flex-direction: column;
    border-right: 1px solid #e0e0e0;
}

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
 }

 .env-add-button{
    flex: 1;
    padding: 10px 5px;
    border: 1px solid #ccc;
    border-radius: 5px;
    cursor: pointer;
    background: #50f9ffff;
    font-size: 12px;
 }

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

.app-result{
    width: 200px;
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
    border-right: 1px solid #e0e0e0;
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