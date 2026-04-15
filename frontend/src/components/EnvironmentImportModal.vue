<template>
  <div v-if="showImportModal" class="modal-overlay" @click="closeImportEnvModal">
    <div class="modal-container" @click.stop>
      <div class="modal-header">
        <h3>Import {{selectedEnvType}} Environment</h3>
        <button class="modal-close" @click="closeImportEnvModal">&times;</button>
      </div>

      <div class="modal-body"> 
        <div class="form-group">
          <label>Import Method:</label>
          <select :value="importEnvMethod" @change="updateImportEnvMethod" class="form-control">
            <option value="requirements">From requirements.txt</option>
            <option value="condapack">From condapack</option>
          </select>
        </div>

        <div v-if="importEnvMethod === 'requirements'" class="import-method-section">
          <div>
            <label>Python Version</label>
            <select :value="pythonVersion" @change="updatePythonVersion" class="form-control">
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
          {{selectedEnvType == 'current' ? currentCreatingEnvStep : targetCreatingEnvStep}}
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
</template>

<script setup>
const emit = defineEmits([
  'closeImportEnvModal',
  'handleRequirementSelect',
  'handleCondapackSelect',
  'createEnvironment',
  'update:importEnvMethod',
  'update:pythonVersion'
]);

defineProps({
  showImportModal: {
    type: Boolean,
    default: false
  },
  selectedEnvType: {
    type: String,
    required: true
  },
  importEnvMethod: {
    type: String,
    default: 'requirements'
  },
  pythonVersion: {
    type: String,
    default: 'python3.8'
  },
  requirementFile: {
    type: Object,
    default: null
  },
  condapackFile: {
    type: Object,
    default: null
  },
  isCreatingCurrentEnv: {
    type: Boolean,
    default: false
  },
  currentCreatingEnvStep: {
    type: String,
    default: ''
  },
  currentEnvCreationProgress: {
    type: Number,
    default: 0
  },
  currentEnvCreationError: {
    type: String,
    default: ''
  },
  isCreatingTargetEnv: {
    type: Boolean,
    default: false
  },
  targetCreatingEnvStep: {
    type: String,
    default: ''
  },
  targetEnvCreationProgress: {
    type: Number,
    default: 0
  },
  targetEnvCreationError: {
    type: String,
    default: ''
  }
});

const closeImportEnvModal = () => {
  emit('closeImportEnvModal');
};

const handleRequirementSelect = (event) => {
  emit('handleRequirementSelect', event);
};

const handleCondapackSelect = (event) => {
  emit('handleCondapackSelect', event);
};

const createEnvironment = () => {
  emit('createEnvironment');
};

const updateImportEnvMethod = (event) => {
  emit('update:importEnvMethod', event.target.value);
};

const updatePythonVersion = (event) => {
  emit('update:pythonVersion', event.target.value);
};
</script>

<style scoped>
.import-method-section {
  margin-top: 15px;
}

.progress-section {
  margin: 15px 0;
}

.progress-label {
  margin-bottom: 5px;
  font-weight: bold;
  color: #555;
}
</style>