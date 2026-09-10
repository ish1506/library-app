type DebugDetails = Record<string, boolean | number | string>

export function debugLog(event: string, details?: DebugDetails) {
  if (import.meta.env.DEV) {
    console.debug(`[library] ${event}`, details)
  }
}
