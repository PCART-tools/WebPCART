import { ref } from 'vue'

// 帮助窗口状态
const showHelp = ref(false)

const showHelpModal = () => {
    showHelp.value = true
}

const closeHelpModal = () => {
    showHelp.value = false
}

export {
    showHelp,
    showHelpModal,
    closeHelpModal
}