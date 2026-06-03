/// <reference types="vitest/config" />
import { defineConfig, mergeConfig } from 'vitest/config'
import viteConfig from './vite.config'

// Test config lives here, separate from vite.config.ts, so the production
// build (`tsc -b && vite build`) never type-checks the Vitest-only `test`
// field against vite's defineConfig overload.
export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: 'jsdom',
      globals: true,
      setupFiles: ['./src/test/setup.ts'],
    },
  }),
)
