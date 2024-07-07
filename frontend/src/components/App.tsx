import "@/styles/App.scss"
import { Config, HistoryRecord, Process, request } from "@/utils/request"
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
      processes.unshift({
        processId: 0,
        name: "all",
        label: "总值",
      })
      manualUpdate()
    }
  }

  async function handleRefreshData() {
    const offset = records.length
    const response = await request.getHistory({
      offset: offset,
      version: version,
    })
    version = response.version ?? version
    const responseRecords = response.history?.records ?? []
    lastUpdate = new Date()
    manualUpdate()
    if (responseRecords.length === 0) {
      setTimeout(handleRefreshData, 1000)
      return
    }
    setTimeout(handleRefreshData, 1000)
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

  function handleRefresh() {
    window.location.reload()
  }

  function handleSwitchTheme() {
    darkMode.toggle()
  }

  useEffect(() => {
    reloadConfig().then(reloadProcesses).then(handleRefreshData)
  }, [])

  const dataPairs = [
    { name: "最后更新", value: lastUpdate.toLocaleString() },
    { name: "进程数量", value: processes.length },
    { name: "总数据量", value: records.length },
    { name: "刷新间隔", value: `${config.pageUpdateIntervalMillis}ms` },
  ]

  const dataArea =
    processes.length === 0 || records.length === 0 ? (
      <center>
        <CircularProgress />
      </center>
    ) : (
      processes.map(makeProcessCard)
    )

  return (
    <>
      <div className="header">
        <div className="title">{config.targetProcessName}</div>
        <div className="right-part">\^O^/</div>
      </div>
      <Card className="data-card">
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
              <Button>保存数据</Button>
              <Button>载入数据</Button>
            </ButtonGroup>
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
