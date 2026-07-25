import { defineConfig } from 'vite'
import { resolve } from 'path'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, './qwen_src')
    }
  },
  define: {
    'process.env.NODE_ENV': JSON.stringify('production')
  },
  build: {
    lib: {
      entry: resolve(__dirname, './qwen_src/main.ts'),
      formats: ['es'],
      fileName: 'lackluster_qwen_multiangle'
    },
    rollupOptions: {
      external: [
        '../../../scripts/app.js',
        '../../../scripts/api.js'
      ],
      output: {
        dir: 'js',
        entryFileNames: 'lackluster_qwen_multiangle.js',
        chunkFileNames: 'assets/[name].js',
        assetFileNames: 'assets/[name][extname]'
      }
    },
    sourcemap: true,
    minify: false,
    cssCodeSplit: false
  }
})
