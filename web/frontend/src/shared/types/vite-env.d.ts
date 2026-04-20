/// <reference types="vite/client" />

declare const __STATIC_ASSETS__: string

declare module '*.hocr' {
  const content: string
  export default content
}

declare module '*.hocr?raw' {
  const content: string
  export default content
}
