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
  CircularProgress,
  Divider,
} from "@nextui-org/react"
import ReactECharts, { EChartsOption } from "echarts-for-react"
import { useEffect, useState } from "react"
import useDarkMode from "use-dark-mode"

let records: HistoryRecord[] = []
let version = 0
let processes: Process[] = []
let config: Config = {} as Config
let lastUpdate = new Date()
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
  const darkMode = useDarkMode(false)
  const manualUpdate = () => setCount((prev) => prev + 1)

  function makeCpuGpuOptionFor(process: Process): EChartsOption {
    const processRecords = records.filter(
      (record) => record.process.processId === process.processId
    )
    const timestamps = processRecords.map((record) =>
      new Date(record.timestampSeconds * 1000).toLocaleString()
    )
    const cpuValues = processRecords.map((record) => record.cpuPercentage)
    const gpuValues = processRecords.map((record) => record.gpuPercentage)
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
      new Date(record.timestampSeconds * 1000).toLocaleString()
    )
    const ussValues = processRecords.map(
      (record) => record.memoryUtilization.uniqueSetSize
    )
    const rssValues = processRecords.map(
      (record) => record.memoryUtilization.residentSetSize
    )
    const vssValues = processRecords.map(
      (record) => record.memoryUtilization.virtualSize
    )

    return {
      ...GenericOptions,
      title: {
        text: "内存占用",
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
      processes.unshift({
        processId: 0,
        name: "all",
        label: "总值",
      })
      if (config.shouldShowTotalOnly) {
        processes = [processes[0]]
      }
      manualUpdate()
    }
  }

  async function handleRefreshData() {
    if (isPaused) {
      setTimeout(handleRefreshData, config.pageUpdateIntervalMillis)
      return
    }

    const offset = records.length
    const response = await request.getHistory({
      offset: offset,
      version: version,
    })
    version = response.version ?? version
    const responseRecords = response.history?.records ?? []
    lastUpdate = new Date()
    manualUpdate()
    reloadProcesses()
    if (responseRecords.length === 0) {
      setTimeout(handleRefreshData, config.pageUpdateIntervalMillis)
      return
    }
    setTimeout(handleRefreshData, config.pageUpdateIntervalMillis)
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
          <ReactECharts
            option={makeMemoryOptionFor(process)}
            style={{ marginTop: "36px" }}
          />
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

  useEffect(() => {
    reloadConfig().then(reloadProcesses).then(handleRefreshData)
    // eslint-disable-next-line
  }, [])

  const dataPairs = [
    { name: "最后更新", value: lastUpdate.toLocaleString() },
    { name: "进程数量", value: processes.length },
    { name: "总数据量", value: records.length },
    { name: "刷新间隔", value: `${config.pageUpdateIntervalMillis}ms` },
  ]

  const dataArea =
    processes.length === 0 ? (
      <center>未检测到目标进程，请先运行 {config.targetProcessName}</center>
    ) : records.length === 0 ? (
      <center>
        <CircularProgress />
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
        <div className="right-part">\^O^/</div>
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
            <Button onClick={handleRefresh}>刷新页面</Button>
            <ButtonGroup>
              <Button onClick={handleDownloadData}>保存数据</Button>
              <Button onClick={handleLoadData}>载入数据</Button>
            </ButtonGroup>
            <Button onClick={() => setPaused(!isPaused)}>
              {isPaused ? "恢复更新" : "暂停更新"}
            </Button>
            <Button onClick={handleClearScreen}>清屏</Button>
          </div>
          <div className="sub-button-area">
            <Button color="danger" onClick={handleSwitchTheme}>
              切换模式
            </Button>
          </div>
        </div>
      </Card>
      {dataArea}
    </>
  )
}

export default App

/// \^O^//
