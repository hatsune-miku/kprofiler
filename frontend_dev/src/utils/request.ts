export interface GetDiagramRequest {
  offset: number
  version: number
}

export interface GetConfigRequest {}

export interface GetHistoryResponse {
  history?: History

  // 如果后端给了version应当更新然后重置offset
  version?: number
}

export interface GetConfigResponse {
  config?: Config
}

export interface GetProcessesResponse {
  processes?: Process[]
}

export interface RequestDownloadResponse {
  fullHistory: string
}

export interface History {
  records: HistoryRecord[]
}

export interface HistoryRecord {
  timestampSeconds: number
  process: Process
  cpuPercentage: number
  gpuPercentage: number
  memoryUtilization: MemoryUtilization
}

export interface Process {
  processId: number
  name: string
  label: string
}

export interface MemoryUtilization {
  /** Unit: MB */
  uniqueSetSize: number

  /** Unit: MB */
  residentSetSize: number

  /** Unit: MB */
  virtualSize: number

  /** Unit: MB */
  workingSet: number

  /** Unit: MB */
  privateWorkingSet: number

  /** Unit: MB */
  systemTotal: number

  /** Unit: MB */
  systemAvailable: number

  /** Unit: MB */
  fromTaskmgr: number

  /** Unit: Bytes */
  vsize: number
}

export interface Config {
  targetProcessName: string
  durationMillis: number
  shouldShowRealtimeDiagram: boolean
  latestRecordCount: number
  pageUpdateIntervalMillis: number
  shouldWriteLogs: boolean
  shouldDisableGpu: boolean
  shouldShowTotalOnly: boolean
  port: number
  historyUpperBound: number
  cpuDurationMillis: number
  gpuDurationMillis: number
  labelCriteria: LabelCriterion[]
}

export interface LabelCriterion {
  keyword: string
  label: string
}

const BaseUrl =
  process.env.NODE_ENV === 'development' ? 'http://localhost:6308' : ''

async function get<T>(url: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(BaseUrl + url)
    return (await response.json()) as T
  } catch {
    return fallback
  }
}

/* eslint-disable @typescript-eslint/no-explicit-any */
async function post<R, T = any>(url: string, data: T): Promise<R> {
  const response = await fetch(BaseUrl + url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
  return (await response.json()) as R
}

export async function getConfig(): Promise<Config> {
  return await get<Config>('/api/config', {} as Config)
}

export async function getHistory(
  request: GetDiagramRequest
): Promise<GetHistoryResponse> {
  return await get<GetHistoryResponse>(
    `/api/history?offset=${request.offset}&version=${request.version}`,
    {}
  )
}

export async function getProcesses(): Promise<GetProcessesResponse> {
  return await get<GetProcessesResponse>('/api/processes', {})
}

export async function downloadHistory(): Promise<RequestDownloadResponse> {
  return await post<RequestDownloadResponse>('/api/download', {})
}

export async function loadHistory(fullHistory: string): Promise<void> {
  await post<GetHistoryResponse>('/api/load', {
    full_history: fullHistory,
  })
}

export async function requestClearHistory(): Promise<void> {
  await post<void>('/api/clear', {})
}

export const request = {
  getConfig,
  getHistory,
  getProcesses,
}
