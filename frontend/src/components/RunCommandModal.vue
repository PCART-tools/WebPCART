<template>
    <!-- 运行命令导入窗口 -->
    <div v-if="showCommandModal" class="modal-overlay" @click="closeCommandModal">
        <div class="modal-container" @click.stop>
            <div class="modal-header">
                <h3>Import Run Command</h3>
                <button class="modal-close" @click="closeCommandModal">&times;</button>
            </div>

            <div class="modal-body">
                <div class="form-group">
                    <label>Select Python File</label>
                    <select
                        v-model="selectedFile"
                        class="form-control"
                        @change="updateCommandPreview">                    
                        <option 
                            v-for="file in pythonFiles"
                            :key="file"
                            :value="file">
                            {{ file }}
                        </option>
                    </select>
                </div>

                <div class="form-group">
                    <label>Command Preview:</label>
                    <div class="command-preview">
                        <span class="command-body">python {{ fileName }}</span>
                        <input
                            type="text"
                            class="additional-args"
                            v-model="additionalArgs"
                            placeholader=""
                            @input="updateCommandPreview"/>
                    </div>
                </div>

                <div class="modal-footer">
                    <button @click="closeCommandModal" class="cancel-button">Close</button>
                    <button
                        class="confirm-button"
                        :disabled="!selectedFile"
                        @click="saveCommand">
                        Save Command
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, watch } from 'vue';                                                                                                                    

const props = defineProps({
  showCommandModal: Boolean,
  project: Object,
  pythonFiles: Array,
  selectedPythonFile: String,
  additionalArgs: String
});

const emit = defineEmits(['closeCommandModal', 'saveCommand']);

const selectedFile = ref(props.selectedPythonFile);
const additionalArgs = ref(props.additionalArgs);
const fullCommand = ref('');
const runFilePath = ref('');
const fileName = ref('');

// 监听 props 变化并更新本地状态
watch(() => props.selectedPythonFile, (newVal) => {
  selectedFile.value = newVal;               
});

watch(() => props.additionalArgs, (newVal) => {
  additionalArgs.value = newVal;      
});

const updateCommandPreview = () => {
  if (selectedFile.value) {
    // 解析路径信息
    const pathParts = selectedFile.value.replace(/\\/g, '/').split('/');

    fileName.value = pathParts.pop();
    const relativePath = pathParts.slice(1).join('/') || ''; 
    
    runFilePath.value = relativePath; 
    fullCommand.value = `python ${fileName.value}${additionalArgs.value ? ' ' + additionalArgs.value : ''}`;
  } else {
    fullCommand.value = '';
  }
};

const closeCommandModal = () => {
  emit('closeCommandModal');
};

const saveCommand = () => {
    emit('saveCommand', fullCommand.value, runFilePath.value);
};
</script>

<style scoped>
.command-preview {
  display: flex;
  align-items: center;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 5px;
  background-color: #f5f5f5;
  font-family: monospace;
}

.command-body {
  color: #2c3e50;
  font-weight: bold;
  white-space: nowrap;
}

.additional-args {
  border: none;
  background: transparent;
  outline: none;
  padding: 0 5px;
  flex: 1;
  font-family: monospace;
}
</style>