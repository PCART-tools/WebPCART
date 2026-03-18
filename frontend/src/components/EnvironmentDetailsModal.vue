<template>
  <div v-if="showEnvDetailsModal" class="modal-overlay" @click="closeEnvDetailsModal">
    <div class="modal-container" @click.stop>
      <div class="modal-header">
        <h3>{{selectedEnvDetailsType}} Environment Details</h3>
        <button class="modal-close" @click="closeEnvDetailsModal">&times;</button>
      </div>

      <div class="modal-body">
        <!-- <div class="form-group">
          <label>Python Version</label>
          <div class="env-detail-value">{{envDetails.pythonVersion}}</div>
        </div> -->

        <div class="form-group">
          <label>Dependencies:</label>
          <div v-if="envDetails.dependencies && envDetails.dependencies.length > 0" class="dependencies-list">
            <div v-for="(dep, index) in envDetails.dependencies" :key="index" class="dependency-item">
              {{dep}}
            </div>
          </div>
          <div v-else class="no-dependencies">No dependencies found</div>
        </div>
      </div>

      <div class="modal-footer">
        <button @click="closeEnvDetailsModal" class="cancel-button">Close</button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  showEnvDetailsModal: {
    type: Boolean,
    default: false
  },
  envDetails: {
    type: Object,
    default: () => ({})
  },
  selectedEnvDetailsType: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['closeEnvDetailsModal']);

const closeEnvDetailsModal = () => {
  emit('closeEnvDetailsModal');
};
</script>

<style scoped>
.dependencies-list {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  padding: 10px;
  background-color: #f8f9fa;
}

.dependency-item {
  padding: 5px 0;
  border-bottom: 1px solid #eee;
  font-family: 'Monaco', 'Consolas', 'Courier New', monospace;
  font-size: 13px;
}

.dependency-item:last-child {
  border-bottom: none;
}

.no-dependencies {
  padding: 8px 12px;
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  color: #6c757d;
  font-style: italic;
}
</style>