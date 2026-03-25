NEW_FILE_CODE

# 基础隔离
net none

blacklist /etc/shadow
blacklist /etc/passwd
blacklist /etc/sudoers
blacklist /etc/ssh
blacklist /root
blacklist /boot
blacklist /dev/mem
blacklist /proc/kcore
blacklist /sys/kernel

whitelist /home/wyh/WebPCART
whitelist /tmp

read-only /
tmpfs /tmp
tmpfs /var/tmp

# 系统调用限制
seccomp
deny_execve    
deny_mount      
deny_ptrace     
deny_sys_admin   
deny_sys_module  
deny_sys_rawio  

# 资源限制
rlimit-nofile 1024
rlimit-cpu 600
rlimit-as 524288
rlimit-core 0
rlimit-nproc 256

# 权限限制
no-new-privileges
noroot
caps.drop all

# 其他安全选项
hidepid
nox11
dbus-user none
dbus-system none
env PYTHONUNBUFFERED=1
env PYTHONDONTWRITEBYTECODE=1
env HOME=/tmp
env PATH=/usr/bin:/bin