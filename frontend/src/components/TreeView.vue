<template>
    <ul class="tree">
        <tree-node 
            v-for="(node, index) in treeData.children"
            :key="index"
            :node="node"
            :project-name="projectName"
            :base-path="''"
            :project-type="projectType || 'original'"
        />
    </ul>
</template>

<script setup>
import { ref, provide } from 'vue';
import TreeNode from './TreeNode.vue'

defineProps(['treeData', 'projectName', 'projectType'])
</script>