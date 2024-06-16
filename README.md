## KProfiler

为 html_pc 项目提供性能监控服务，支持以下功能：

- CPU 占用率采集
- GPU 占用率采集
- RAM 数值采集
- 写入到 csv
- 可视化

## 食用方法

### 1. 安装依赖

```bash
git clone https://github.com/hatsune-miku/kprofiler.git
cd kprofiler
pip install -r requirements.txt
```

### 2. 启动 html_pc 项目

### 3. （可以跳过）修改配置文件 `config.yaml`

点开 `config.yaml` 文件后，按注释修改配置文件。

### 4. 启动 KProfiler

```bash
python main.py
# 或者双击 start.bat
# 或者右键 start.bat 然后管理员权限运行
```

## Demo

以同样基于 electron 的微信小程序 PC 版为例：

![Demo 1](doc/demo1.jpg)
