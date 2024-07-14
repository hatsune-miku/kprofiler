import "@/styles/App.scss"
import {
  Config,
  downloadHistory,
  HistoryRecord,
  loadHistory,
  Process,
  request,
  requestClearHistory,
} from "@/utils/request"
import {
  Button,
  ButtonGroup,
  Card,
  Chip,
  Divider,
  Input,
  Kbd,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  Tooltip,
  useDisclosure,
} from "@nextui-org/react"
import ReactECharts, { EChartsOption } from "echarts-for-react"
import { useEffect, useState } from "react"
import useDarkMode from "use-dark-mode"
import SSProgress from "./SSProgress"

let records: HistoryRecord[] = []
let version = 0
let processes: Process[] = []
let config: Config = {} as Config
let isPaused = false

const GenericOptions: EChartsOption = {
  animation: false,
  dataZoom: {
    type: "slider",
    zoomOnMouseWheel: true,
    maxValueSpan: 2000,
  },
  tooltip: {
    trigger: "axis",
    axisPointer: {
      type: "cross",
      label: {
        backgroundColor: "rgb(213, 82, 118)",
      },
    },
  },
  toolbox: {
    show: true,
    feature: {
      dataView: { readOnly: false },
      restore: {},
      saveAsImage: {},
    },
  },
}

function App() {
  const [count, setCount] = useState(0)
  const [lastUpdate, setLastUpdate] = useState(new Date())
  const darkMode = useDarkMode(false)
  const [minutesInput, setMinutesInput] = useState("")
  const [pauseAt, setPauseAt] = useState(0)
  const {
    isOpen: shouldConfirmOpen,
    onOpen: openConfirm,
    onOpenChange: onConfirmOpenChanged,
  } = useDisclosure()
  const manualUpdate = () => setCount((prev) => prev + 1)

  function makeCpuGpuOptionFor(process: Process): EChartsOption {
    const processRecords = records.filter(
      (record) => record.process.processId === process.processId
    )
    const timestamps = processRecords.map((record) =>
      new Date(record.timestampSeconds * 1000).toLocaleString()
    )
    const cpuValues = processRecords.map((record) =>
      record.cpuPercentage.toFixed(2)
    )
    const gpuValues = processRecords.map((record) =>
      record.gpuPercentage.toFixed(2)
    )
    return {
      ...GenericOptions,
      title: {
        text: "CPU & GPU 占用率",
      },
      xAxis: {
        type: "category",
        data: timestamps,
      },
      yAxis: {
        type: "value",
      },
      series: [
        {
          name: "CPU %",
          data: cpuValues,
          type: "line",
          lineStyle: { color: "rgb(81, 132, 178)" },
          large: true,
          markLine: {
            data: [
              {
                type: "average",
                name: "平均值",
                lineStyle: { color: "rgb(81, 132, 178)" },
              },
            ],
          },
          markPoint: {
            data: [
              {
                type: "max",
                name: "最大值",
                itemStyle: { color: "rgb(81, 132, 178)" },
              },
              {
                type: "min",
                name: "最小值",
                itemStyle: { color: "rgb(81, 132, 178)" },
              },
            ],
          },
        },
        {
          name: "GPU %",
          data: gpuValues,
          type: "line",
          lineStyle: { color: "rgb(241, 167, 181)" },
          large: true,
          markLine: {
            data: [
              {
                type: "average",
                name: "平均值",
                lineStyle: { color: "rgb(241, 167, 181)" },
              },
            ],
          },
          markPoint: {
            data: [
              {
                type: "max",
                name: "最大值",
                itemStyle: { color: "rgb(241, 167, 181)" },
              },
              {
                type: "min",
                name: "最小值",
                itemStyle: { color: "rgb(241, 167, 181)" },
              },
            ],
          },
        },
      ],
      color: ["rgb(81, 132, 178)", "rgb(241, 167, 181)"],
      legend: {
        data: ["CPU %", "GPU %"],
      },
    }
  }

  function makeMemoryOptionFor(process: Process): EChartsOption {
    const processRecords = records.filter(
      (record) => record.process.processId === process.processId
    )
    const timestamps = processRecords.map((record) =>
      new Date(record.timestampSeconds * 1000).toDateString()
    )
    const ussValues = processRecords.map((record) =>
      record.memoryUtilization.uniqueSetSize.toFixed(2)
    )
    const rssValues = processRecords.map((record) =>
      record.memoryUtilization.residentSetSize.toFixed(2)
    )
    const vssValues = processRecords.map((record) =>
      record.memoryUtilization.virtualSize.toFixed(2)
    )

    return {
      ...GenericOptions,
      title: {
        text: "内存占用 (MB)",
      },
      xAxis: {
        type: "category",
        data: timestamps,
      },
      yAxis: {
        type: "value",
      },
      series: [
        {
          name: "USS",
          data: ussValues,
          type: "line",
          lineStyle: { color: "rgb(213, 82, 118)" },
          large: true,
          markLine: {
            data: [
              {
                type: "average",
                name: "平均值",
                lineStyle: { color: "rgb(213, 82, 118)" },
              },
            ],
          },
          markPoint: {
            data: [
              {
                type: "max",
                name: "最大值",
                itemStyle: { color: "rgb(213, 82, 118)" },
              },
              {
                type: "min",
                name: "最小值",
                itemStyle: { color: "rgb(213, 82, 118)" },
              },
            ],
          },
        },
        {
          name: "RSS",
          data: rssValues,
          type: "line",
          lineStyle: { color: "rgb(230, 186, 60)" },
          large: true,
          markLine: {
            data: [
              {
                type: "average",
                name: "平均值",
                lineStyle: { color: "rgb(230, 186, 60)" },
              },
            ],
          },
          markPoint: {
            data: [
              {
                type: "max",
                name: "最大值",
                itemStyle: { color: "rgb(230, 186, 60)" },
              },
              {
                type: "min",
                name: "最小值",
                itemStyle: { color: "rgb(230, 186, 60)" },
              },
            ],
          },
        },
        {
          name: "VSS",
          data: vssValues,
          type: "line",
          lineStyle: { color: "rgb(170, 212, 248)" },
          large: true,
          markLine: {
            data: [
              {
                type: "average",
                name: "平均值",
                lineStyle: { color: "rgb(170, 212, 248)" },
              },
            ],
          },
          markPoint: {
            data: [
              {
                type: "max",
                name: "最大值",
                itemStyle: { color: "rgb(170, 212, 248)" },
              },
              {
                type: "min",
                name: "最小值",
                itemStyle: { color: "rgb(170, 212, 248)" },
              },
            ],
          },
        },
      ],
      color: ["rgb(213, 82, 118)", "rgb(230, 186, 60)", "rgb(170, 212, 248)"],
      legend: {
        data: ["USS", "RSS", "VSS"],
      },
    }
  }

  async function reloadConfig() {
    config = await request.getConfig()
    manualUpdate()
  }

  async function reloadProcesses() {
    const result = await request.getProcesses()
    if (result.processes) {
      processes = result.processes
      if (processes.length === 0) {
        return
      }
      processes.unshift(
        {
          processId: 0,
          name: "all",
          label: "总值",
        },
        {
          processId: 4,
          name: "systemwide",
          label: "整个系统",
        }
      )
      if (config.shouldShowTotalOnly) {
        processes = [processes[0]]
      }
      manualUpdate()
    }
  }

  async function handleRefreshData() {
    const scheduleNextCall = () =>
      setTimeout(handleRefreshData, config.pageUpdateIntervalMillis)

    if (pauseAt !== 0 && new Date().getTime() > pauseAt) {
      setPauseAt(0)
      setPaused(true)
      scheduleNextCall()
      return
    }

    if (isPaused) {
      scheduleNextCall()
      return
    }

    const offset = records.length
    const response = await request.getHistory({
      offset: offset,
      version: version,
    })
    version = response.version ?? version
    const responseRecords = response.history?.records ?? []
    setLastUpdate(new Date())
    reloadProcesses()
    if (responseRecords.length === 0) {
      scheduleNextCall()
      return
    }
    scheduleNextCall()
    records = [...records, ...responseRecords]
  }

  function makeProcessCard(process: Process, i: number) {
    return (
      <>
        <div key={i}>
          <Chip className="chip">
            {process.label}{" "}
            {process.processId !== 0 && `(PID: ${process.processId})`}
          </Chip>
          <ReactECharts option={makeCpuGpuOptionFor(process)} />
          {process.processId !== 4 && (
            <ReactECharts
              option={makeMemoryOptionFor(process)}
              style={{ marginTop: "36px" }}
            />
          )}
        </div>
        <Divider className="divider" />
      </>
    )
  }

  function setPaused(value: boolean) {
    isPaused = value
    manualUpdate()
  }

  function handleRefresh() {
    window.location.reload()
  }

  function handleDownloadData() {
    downloadHistory().then((response) => {
      const historyFullText = response.fullHistory
      downloadString(
        `history-${config.targetProcessName}.csv`,
        "text/csv",
        historyFullText
      )
    })
  }

  function downloadString(filename: string, mimeType: string, text: string) {
    const pom = document.createElement("a")
    pom.setAttribute(
      "href",
      `data:${mimeType};charset=utf-8,` + encodeURIComponent(text)
    )
    pom.setAttribute("download", filename)
    pom.click()
  }

  function handleClearScreen() {
    records = []
    manualUpdate()
    requestClearHistory()
  }

  function handleLoadData() {
    setPaused(false)
    openFile().then((file) => {
      file.text().then((text) => {
        records = []
        loadHistory(text).then(() => {
          setTimeout(() => {
            setPaused(true)
          }, config.pageUpdateIntervalMillis)
        })
      })
    })
  }

  function openFile(): Promise<File> {
    const input = document.createElement("input")
    input.type = "file"
    const ret = new Promise((resolve, reject) => {
      input.onchange = () => {
        const files = input.files
        if (!files || files.length === 0) {
          reject("No file selected")
          return
        }
        resolve(files[0])
      }
    })
    input.click()
    return ret as Promise<File>
  }

  function handleSwitchTheme() {
    darkMode.toggle()
  }

  function handleToggleCountdown() {
    const isCountingDown = pauseAt !== 0
    if (isCountingDown) {
      setPauseAt(0)
      return
    }
    const currentTimestampMillis = new Date().getTime()
    try {
      const minutes = Number.parseInt(minutesInput)
      if (Number.isSafeInteger(minutes)) {
        setPauseAt(currentTimestampMillis + minutes * 60 * 1000)
      }
    } catch {
      setPauseAt(0)
      setMinutesInput("")
    }
  }

  useEffect(() => {
    reloadConfig().then(reloadProcesses).then(handleRefreshData)
    // eslint-disable-next-line
  }, [])

  const dataPairs = [
    { name: "最后更新", value: lastUpdate.toLocaleString() },
    { name: "进程数量", value: processes.length },
    { name: "总数据量", value: records.length },
    {
      name: "刷新间隔",
      value: config.pageUpdateIntervalMillis
        ? `${config.pageUpdateIntervalMillis}ms`
        : "N/A",
    },
  ]

  const dataArea =
    processes.length === 0 ? (
      <center>
        <SSProgress className="progress" />
        等待目标 {config.targetProcessName} 运行...
      </center>
    ) : records.length === 0 ? (
      <center>
        <SSProgress className="progress" />
        暂无数据，初次加载数据会有点慢~
      </center>
    ) : (
      processes.map(makeProcessCard)
    )

  return (
    <>
      <div className="header">
        <div className="title">
          {config.targetProcessName} {isPaused && <Chip>已暂停更新</Chip>}
        </div>
        <div className="right-part">&#9825; KProfiler \^O^/</div>
      </div>
      <Card className="data-card" key={count}>
        <div className="data-area">
          {dataPairs.map((pair, i) => (
            <div key={i} className="data-pair">
              <div className="data-title">{pair.name}</div>
              <div className="data-value">{pair.value}</div>
            </div>
          ))}
        </div>
        <Divider className="divider" />
        <div className="button-area">
          <div className="sub-button-area">
            <Tooltip
              color="danger"
              content={
                <span>
                  等效于 <Kbd>F5</Kbd>, <Kbd>Ctrl+R</Kbd> 或是{" "}
                  <Kbd keys={["command"]}>R</Kbd>
                </span>
              }
            >
              <Button onClick={handleRefresh}>刷新页面</Button>
            </Tooltip>
            <ButtonGroup>
              <Button onClick={handleDownloadData}>保存数据</Button>
              <Button onClick={handleLoadData}>载入数据</Button>
            </ButtonGroup>
            <Tooltip
              color="danger"
              content="仅仅暂停本前端的数据更新。恢复后，会一口气同步暂停期间的所有数据。"
            >
              <Button onClick={() => setPaused(!isPaused)}>
                {isPaused ? "恢复更新" : "暂停更新"}
              </Button>
            </Tooltip>
            <Button onClick={openConfirm}>清屏</Button>
          </div>
          <div className="sub-button-area">
            <Input
              label="计时"
              disabled={pauseAt !== 0}
              placeholder="输入分钟数"
              endContent={
                <Button size="sm" onClick={handleToggleCountdown}>
                  {pauseAt !== 0 ? "停止计时" : "开始计时"}
                </Button>
              }
              value={
                pauseAt !== 0
                  ? `将于 ${new Date(pauseAt).toTimeString()} 结束`
                  : minutesInput
              }
              onChange={(e) => setMinutesInput(e.target.value)}
              size="sm"
            />
          </div>
          <div className="sub-button-area">
            <Button color="danger" onClick={handleSwitchTheme}>
              切换模式
            </Button>
          </div>
        </div>
      </Card>
      {dataArea}
      <Modal isOpen={shouldConfirmOpen} onOpenChange={onConfirmOpenChanged}>
        <ModalContent>
          {(closeConfirm) => (
            <>
              <ModalHeader className="flex flex-col gap-1">
                清空数据
              </ModalHeader>
              <ModalBody>
                <p>确定要清空数据吗？</p>
                <p>
                  这会导致
                  <span style={{ color: "red", fontWeight: "bold" }}>
                    服务端历史记录清空
                  </span>
                  ，所有前端都会受到影响。
                </p>
              </ModalBody>
              <ModalFooter>
                <Button
                  color="danger"
                  onPress={() => {
                    closeConfirm()
                    handleClearScreen()
                  }}
                >
                  清空
                </Button>
                <Button onPress={closeConfirm}>取消</Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>
    </>
  )
}

export default App

/// \^O^//
