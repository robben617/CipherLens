import { mkdtempSync } from 'node:fs'
import { createRequire } from 'node:module'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const require = createRequire(new URL('../../frontend/package.json', import.meta.url))
const esbuild = require('esbuild')

const entry = fileURLToPath(new URL('../../frontend/src/engine/trace.ts', import.meta.url))
const outfile = join(mkdtempSync(join(tmpdir(), 'cipherlens-')), 'trace.mjs')

esbuild.buildSync({
  entryPoints: [entry],
  bundle: true,
  format: 'esm',
  platform: 'node',
  outfile,
})

const { buildTrace } = await import(pathToFileURL(outfile).href)
const plaintext = process.argv[2] ?? '00112233445566778899aabbccddeeff'
const key = process.argv[3] ?? '000102030405060708090a0b0c0d0e0f'
const trace = buildTrace({ plaintext, key })

process.stdout.write(JSON.stringify(trace))