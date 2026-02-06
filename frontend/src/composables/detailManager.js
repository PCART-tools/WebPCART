 import { ref } from 'vue'
import { project } from './projectManager'
import { showNotification } from './utils'

// 报告相关状态
const reportData = ref(null)
const isGeneratingReport = ref(false)

// API详情模态框相关状态
const showAPIDetailModal = ref(false);
const selectedAPIDetail = ref({});

// 获取报告数据
export const getReport = async () => {
  if (!project.value) {
    showNotification('No project selected', 'error');
    return;
  }

  try {
    isGeneratingReport.value = true;

    const encodedProjectName = encodeURIComponent(project.value);
    const response = await fetch(`http://localhost:5000/report/${encodedProjectName}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (response.ok) {
      const result = await response.json();
      reportData.value = result.data;
      showNotification(`report loaded`, 'success');
    } else {
      showNotification(`Failed to load report`, 'error');
    }
  } catch (error) {
    console.error(`Error fetching report:`, error);
    showNotification(`Error loading report: ${error.message}`, 'error');
  } finally {
    isGeneratingReport.value = false;
  }
}

const showAPIDetail = (apiDetail) => {
    selectedAPIDetail.value = apiDetail;
    showAPIDetailModal.value = true;
};

const closeAPIDetailModal = () => {
    showAPIDetailModal.value = false;
    selectedAPIDetail.value = {};
};

// 导出相关状态和方法
export {
  reportData,
  isGeneratingReport,
  showAPIDetail,
  selectedAPIDetail,
  closeAPIDetailModal,
  showAPIDetailModal
}