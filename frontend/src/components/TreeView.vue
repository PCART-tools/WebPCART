<template>
    <ul class="tree">
        <tree-node 
            v-for="(node, index) in treeData.children"
            :key="index"
            :node="node"
            :project-name="projectName"
            :base-path="''"
        />
    </ul>
</template>

<script setup>
import TreeNode from './TreeNode.vue'

defineProps(['treeData', 'projectName'])
</script>