import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { resolve } from 'path';

export default defineConfig(({ mode }) => {
  const isLibrary = process.env.BUILD_MODE === 'library';
  const isSDK = process.env.BUILD_MODE === 'sdk';
  const isWidget = process.env.BUILD_MODE === 'widget';

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': resolve(__dirname, '.'),
        'widget': resolve(__dirname, 'widget'),
        'shared': resolve(__dirname, 'shared'),
        'sdk': resolve(__dirname, 'sdk'),
      },
    },
    css: {
      preprocessorOptions: {
        scss: {
          api: 'modern-compiler'
        }
      }
    },
    build: {
      lib: isLibrary ? {
        entry: {
          sdk: resolve(__dirname, isSDK ? 'build/sdk.js' : 'build/widget.js'),
        },
        name: 'EchoPilotWidget',
        formats: ['iife'],
      } : false,
      rollupOptions: {
        input: isLibrary ? undefined : {
          sdk: resolve(__dirname, 'build/sdk.js'),
          widget: resolve(__dirname, 'build/widget.js'),
        },
        output: isLibrary ? {
          entryFileNames: '[name].js',
          assetFileNames: '[name][extname]',
          globals: {
            vue: 'Vue',
          },
        } : {
          entryFileNames: 'assets/[name]-[hash].js',
          chunkFileNames: 'assets/[name]-[hash].js',
          assetFileNames: 'assets/[name]-[hash][extname]',
        },
        external: isLibrary ? [] : undefined,
      },
      outDir: 'dist',
      emptyOutDir: true,
      sourcemap: mode === 'development',
    },
    server: {
      port: 3000,
      host: true,
    },
  };
});