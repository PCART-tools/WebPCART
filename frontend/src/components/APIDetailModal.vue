<template>
  <div v-if="show" class="modal-overlay" @click="closeModal">
    <div class="modal-container api-detail-modal" @click.stop style="width: 60%; max-width: 800px;">
      <div class="modal-header">
        <h3>API Detail Information</h3>
        <button class="modal-close" @click="closeModal">&times;</button>
      </div>

      <div class="modal-body">
        <div class="detail-item">
          <label>API Call:</label>
          <pre class="api-call">{{ apiDetail.invoked_api }}</pre>
        </div>

        <div class="detail-item">
          <label>Location:</label>
          <div class="location">{{ apiDetail.location }}</div>
        </div>

        <div class="detail-item">
          <label>Coverage:</label>
          <div class="coverage">{{ apiDetail.coverage }}</div>
        </div>

        <div v-if="apiDetail.coverage === 'Yes'" class="definitions-section">
          <h4>Definitions</h4>
          <div class="definitions-compare">
            <div class="definition-column">
              <label>Version 1 Definition:</label>
              <pre class="definition">{{ apiDetail.definition_v1 }}</pre>
            </div>
            <div class="definition-column">
              <label>Version 2 Definition:</label>
              <pre class="definition">{{ apiDetail.definition_v2 }}</pre>
            </div>
          </div>
        </div>

        <div v-if="apiDetail.coverage === 'Yes'" class="status-section">
          <div class="status-item">
            <label>Compatibility Status:</label>
            <span :class="apiDetail.compatible ? 'status-compatible' : 'status-incompatible'">
              {{ apiDetail.compatible ? 'Compatible' : 'Incompatible' }}
            </span>
          </div>
        </div>

        <div v-if="apiDetail.coverage === 'Yes' && !apiDetail.compatible" class="repair-section">
          <div class="repair-item">
            <label>Repair Status:</label>
            <span class="repair-status">{{ apiDetail.repair_status || 'N/A' }}</span>
          </div>
          <div class="repair-item">
            <label>Repair Result:</label>
            <pre class="repair-result">{{ apiDetail.repair_result || 'N/A' }}</pre>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button @click="closeModal" class="cancel-button">Close</button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  show: {
    type: Boolean,
    default: false
  },
  apiDetail: {
    type: Object,
    default: () => ({})
  }
});

const emit = defineEmits(['close']);

const closeModal = () => {
  emit('close');
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.api-detail-modal {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  padding: 16px 24px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.modal-close:hover {
  color: #333;
}

.modal-body {
  padding: 24px;
}

.detail-item {
  margin-bottom: 20px;
}

.detail-item label {
  display: block;
  font-weight: bold;
  margin-bottom: 5px;
  color: #555;
}

.api-call, .definition, .repair-result {
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  padding: 12px 15px;
  font-family: 'Monaco', 'Consolas', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 180px;
  overflow-y: auto;
  tab-size: 4;
  -moz-tab-size: 4;
  -o-tab-size: 4;
}

.location, .coverage {
  padding: 8px 12px;
  background-color: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

.definitions-section {
  margin: 20px 0;
}

.definitions-section h4 {
  margin: 0 0 15px 0;
  color: #333;
  border-bottom: 1px solid #eee;
  padding-bottom: 5px;
}

.definitions-compare {
  display: flex;
  gap: 15px;
  flex-direction: column;
}

.definition-column {
  flex: 1;
}

.definition-column label {
  font-weight: bold;
  color: #555;
  margin-bottom: 5px;
  display: block;
}

.status-section, .repair-section {
  margin: 20px 0;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.status-item, .repair-item {
  margin-bottom: 15px;
}

.status-item label, .repair-item label {
  font-weight: bold;
  color: #555;
  margin-bottom: 5px;
  display: block;
}

.status-compatible {
  color: #28a745;
  font-weight: bold;
  background-color: #e6ffec;
  padding: 2px 6px;
  border-radius: 3px;
}

.status-incompatible {
  color: #dc3545;
  font-weight: bold;
  background-color: #ffecec;
  padding: 2px 6px;
  border-radius: 3px;
}

.repair-status {
  padding: 2px 6px;
  border-radius: 3px;
  background-color: #f0f0f0;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: flex-end;
}

.cancel-button {
  padding: 8px 16px;
  background-color: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.cancel-button:hover {
  background-color: #5a6268;
}
</style>