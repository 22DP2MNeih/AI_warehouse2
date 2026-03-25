<script setup>
import { computed } from 'vue';
const windows = computed(() => [
    "part view",
    "Settings",
    "bla bla"
]);
</script>

<template>
    <nav>
        <div v-for="value in windows" :key="value">
            <router-link to="/" class="nav-link" @click="closeMenu">{{value}}</router-link>
        </div>
    </nav>

</template>

<style scoped>
nav {
    width: 100%;
    height: 10rem;
    background-color: var(--background_color1);
}
</style>