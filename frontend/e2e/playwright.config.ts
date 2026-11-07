import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: '.',
  timeout: 30000,
  fullyParallel: false,
  workers: 1,
  reporter: [['list']],
  outputDir: '../../output/playwright',
  use: {
    baseURL: 'http://127.0.0.1:8080',
    channel: 'chrome',
    headless: true,
    viewport: { width: 1440, height: 900 },
    trace: 'off',
  },
})