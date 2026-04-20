import { readFile } from 'node:fs/promises'
import type { Plugin } from 'vite'

const WINDOWS_DRIVE_PREFIX = /^\/[A-Za-z]:\//

function toFilePath(id: string) {
  const [cleanId] = id.split('?')

  if (cleanId.startsWith('/@fs/')) {
    return decodeURIComponent(cleanId.slice('/@fs/'.length))
  }

  if (WINDOWS_DRIVE_PREFIX.test(cleanId)) {
    return decodeURIComponent(cleanId.slice(1))
  }

  return decodeURIComponent(cleanId)
}

export function hocrTextPlugin(): Plugin {
  return {
    name: 'hocr-text-plugin',
    enforce: 'pre',
    async load(id) {
      const filePath = toFilePath(id)

      if (!filePath.endsWith('.hocr')) {
        return null
      }

      const content = await readFile(filePath, 'utf8')

      return `export default ${JSON.stringify(content)};`
    },
  }
}

