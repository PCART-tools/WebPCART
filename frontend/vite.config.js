import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools()
  ],
  resolve:{
    alias:{
      '@':fileURLToPath(new URL('./src',import.meta.url)),
      'vue': 'vue/dist/vue.esm-bundler.js'
    }
  },
  server:{
    host: '0.0.0.0',
    port: 5173,
    proxy:{
      '/project':{
        target:'http://localhost:5000',
        changeOrigin:true,
        secure: false
      },
      '/fix':{
        target:'http://localhost:5000',
        changeOrigin:true,
        secure: false
      },
      '/venv':{
        target:'http://localhost:5000',
        changeOrigin:true,
        secure: false
      },
      '/report':{
        target:'http://localhost:5000',
        changeOrigin:true,
        secure: false
      }
    }
  },
  optimizeDeps:{
    include: ['monaco-editor']
  },
  define: {
    global: 'globalThis',
  }
})