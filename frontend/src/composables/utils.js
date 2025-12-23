// 消息弹窗功能
export const showNotification = (message, type) => {
    const notification = document.createElement('div');
    notification.textContent = message;

    notification.style.position = 'fixed';
    notification.style.left = '50%';
    notification.style.top = '20px';
    notification.style.borderRadius = '5px';
    notification.style.color = 'white';
    notification.style.zIndex = '9999';
    notification.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.2)'
    notification.style.transition = 'all 0.3s ease'
    notification.style.opacity = '0'
    notification.style.transform = 'translateX(-50%)'
    notification.style.fontSize = '20px'

    if(type === 'success'){
        notification.style.backgroundColor = '#4CAF50'
    }else if(type === 'warning'){
        notification.style.backgroundColor = '#FFC107'
    }else{
        notification.style.backgroundColor = '#F44336'
    }
    

    document.body.appendChild(notification);

    setTimeout(() =>{
        notification.style.opacity = '1';
        notification.style.transform = 'translateY(0)';
    }, 10);

    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(20px)';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 2000);
}