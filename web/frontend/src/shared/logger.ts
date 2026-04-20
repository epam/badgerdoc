/* eslint-disable no-console */

type LogArgs = unknown[]

export const logger = {
  debug: (...args: LogArgs) => {
    console.log(...args)
  },
  warn: (...args: LogArgs) => {
    console.warn(...args)
  },
  error: (...args: LogArgs) => {
    console.error(...args)
  },
}
