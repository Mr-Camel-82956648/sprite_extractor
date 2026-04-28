# Sprite Extractor

将 MP4 视频转换为 HTML 游戏可用的动作序列帧。提供可视化 Web 工具完成抽帧、帧选择、循环预览、命名导出的全流程。

## 快速开始

```bash
cd d:\projects\sprite_extractor

# 首次使用：创建虚拟环境
python -m venv venv
venv\Scripts\pip install flask opencv-python

# 启动
venv\Scripts\python server.py
```

浏览器打开 http://localhost:5000

## 使用流程

1. **将视频放入 `source_videos/`**（支持 mp4/avi/mov/webm）
2. **选择视频 & 抽帧** — 设置每 N 帧取 1 帧的频率
3. **选择帧** — 点击选择有效帧，去掉开头停顿和重复帧（支持 Shift+点击范围选择）
4. **循环预览** — 调节 FPS 预览动画效果，确认动作连贯
5. **命名 & 导出 ZIP** — 填写角色名、方向、动作，下载自动命名的 PNG 包
   - 命名格式：`{角色}_{方向}_{动作}_{序号}.png`
   - 示例：`player1_front_right_run_01.png`
6. **外部抠图** — 将 ZIP 内的图片上传到抠图工具批量去背景
7. **导入结果** — 将抠图后的 PNG 拖入页面，自动保存到 `output/` 并预览

## 目录结构

```
sprite_extractor/
├── source_videos/   # 原始视频
├── frames/          # 抽帧中间产物（自动生成）
├── export/          # 导出目录
├── output/          # 最终序列帧（抠图后导入）
├── server.py        # Flask 后端
├── index.html       # 前端工具页面
└── venv/            # Python 虚拟环境
```

## 依赖

- Python 3.10+
- Flask
- OpenCV (opencv-python)
