# Sprite Extractor

把角色动作视频拆成逐帧 PNG，并通过网页完成选帧、预览、导出、导入抠图结果和尺寸统一。

## 启动

### 1. 准备环境

- Python 3.10+
- Windows PowerShell 或 `cmd`

### 2. 进入项目目录

```powershell
cd D:\projects\sprite_extractor
```

### 3. 创建虚拟环境

```powershell
python -m venv venv
```

### 4. 安装依赖

```powershell
venv\Scripts\python -m pip install flask opencv-python numpy
```

### 5. 启动服务

```powershell
venv\Scripts\python server.py
```

浏览器打开 `http://127.0.0.1:5000`

如果你已经手动激活了虚拟环境，也可以直接运行：

```powershell
python server.py
```

## 首次使用

1. 把待处理视频放进 `source_videos/`
2. 在网页第 1 步选择视频并抽帧
3. 在第 2 步筛掉不需要的帧
4. 在第 3 步预览动画节奏
5. 在第 4 步填写角色名、方向、动作并导出 ZIP
6. 去第三方抠图工具批量去背景后，把结果拖回第 5 步导入
7. 如果同一角色有多个动作，在第 6 步统一缩放和偏移

## 目录说明

```text
sprite_extractor/
|-- source_videos/   原始视频
|-- frames/          抽帧后的中间文件
|-- output/          导入抠图结果和归一化结果
|-- export/          导出的 ZIP
|-- server.py        Flask 后端
`-- index.html       前端页面
```

## 说明

- 支持的视频格式：`.mp4`、`.avi`、`.mov`、`.webm`
- 当前版本已兼容中文视频文件名的抽帧与预览
- `frames/` 是中间产物，必要时可以删除后重新抽帧
