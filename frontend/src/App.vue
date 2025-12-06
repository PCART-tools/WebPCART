<template>
    <div class="app-container">
        <!-- 功能栏 -->
        <div class="function-bar">
        <b>功能栏</b>
        </div>

        <!-- 网页主体 -->
        <div class="app-main">
            <!-- 项目管理栏 -->
            <div class="app-project">
            <b>项目管理栏</b>
            </div>

            <div class="app-middle">
                <!-- 虚拟环境配置栏 -->
                <div class="app-env">
                <b>虚拟环境管理栏</b>
                </div>

                <!-- 代码编辑栏 -->
                <div class="app-code">
                <b>代码编辑栏</b>
                </div>
            </div>

            <!-- 运行结果栏 -->
            <div class="app-result">
            <b>运行结果栏</b>
            </div>
        </div>
    </div>
</template>

<script>
</script>

<style>
.app-container{ 
    width: 100vw;
    height: 100vh;
    display: flex;
    flex-direction: column;
    border: 1px solid black;
}

.function-bar{
    height: 40px;
    border-bottom: 1px solid black;
    background: #e0e0e0;
    padding-left: 10px;
    font-weight: bold;
}

.app-main{
    flex: 1;
    display: flex;
    height: calc(100vh - 40px);
}

.app-project{
    width: 120px;
    border-right: 1px solid black;
    padding: 10px;
    position: relative;
}

.app-middle{
    flex: 1;
    display: flex;
    flex-direction: column;
    border-right: 1px solid black;
}

.app-env{
    height: 40px;
    padding: 10px;
    border-bottom: 1px solid black;
    positon: relative;
}

.app-code{
    flex: 1;
    padding: 10px;
}

.app-result{
    width: 200px;
    position: relative;
}

</style>