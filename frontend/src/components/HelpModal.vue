<template>
  <div v-if="show" class="modal-overlay" @click="closeModal">
    <div class="modal-container help-modal" @click.stop style="width: 60%; max-width: 800px;">
      <div class="modal-header">
        <h3>Help</h3>
        <button class="modal-close" @click="closeModal">&times;</button>
      </div>

      <div class="modal-body">
        <div class="help-section">
          <h4>Functionality</h4>
          <p>WebPCART is a web-based tool designed to analyze Python code compatibility across different library versions and environments. It helps developers identify, analyze, and repair compatibility issues when upgrading or migrating Python libraries.</p>
        </div>

        <div class="help-section">
          <h4>How to Use</h4>
          <ol class="usage-steps">
            <li><strong>Import Project</strong>: Click the "+" button in the Projects section to upload your Python project directory.</li>
            <li><strong>Configure Environments</strong>: Set up both current and target virtual environments by importing requirements.txt files or conda-pack archives.</li>
            <li><strong>Select Library</strong>: Choose the library you want to analyze for compatibility issues from the dropdown menu.</li>
            <li><strong>Set Run Command</strong>: Specify the command used to run your project for dynamic analysis.</li>
            <li><strong>Run Analysis</strong>: Click the "Run" button to start the compatibility analysis process.</li>
            <li><strong>View Results</strong>: After completion, you can view results:
              <ul class="result-details">
                <li><strong>Compatibility Report</strong>: Review the detailed compatibility report showing covered APIs, compatibility status, and repair suggestions in the main panel.</li>
                <li><strong>Repaired Project</strong>: Browse the repaired project files in the left Projects panel to see the source code after automatic repairs have been applied.</li>
                <li><strong>Instrumented Project</strong>: Explore the instrumented project (marked with "-instrument" suffix) in the left Projects panel to examine the dynamically analyzed code that was used during the compatibility analysis process.</li>
              </ul>
            </li>
            <li><strong>Edit Files</strong>: Click on any file in either the original or repaired project tree to view and edit its content directly in the built-in code editor.</li>
          </ol>
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

.help-modal {
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
  padding: 24px 32px;
}

.help-section {
  margin-bottom: 28px;
}

.help-section h4 {
  margin: 0 0 18px 0;
  color: #333;
  border-bottom: 1px solid #eee;
  padding-bottom: 8px;
  font-size: 1.1em;
}

.help-section p {
  line-height: 1.6;
  color: #555;
  margin-bottom: 0;
}

.usage-steps {
  padding-left: 15px;
  line-height: 1.8;
  color: #555;
  margin: 0;
}

.usage-steps li {
  margin-bottom: 16px;
}

.result-details {
  padding-left: 28px;
  margin-top: 12px;
  line-height: 1.7;
  margin-bottom: 0;
}

.result-details li {
  margin-bottom: 10px;
}

.help-section strong {
  color: #333;
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