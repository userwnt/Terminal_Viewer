# v0.0.1

- 第一个版本

# v0.0.2

> 记不清什么时候了

- 改进缓存策略
- 新增依赖：`cachetools`

> 2026年8月20日 12:33:40

- 新增函数：`parse_frames` `play_parsed_video` `show_parsed_photo`
- 新增的这些函数也带来了更多有意思玩法，例如**解析后对帧数据进行优化**，**多进程解析**之类的
- 还有使用`play_parsed_video`播放的视频貌似比`play_video`更流畅？🤔

> 2026年8月21日 12:13:40

- 新增`demo`文件夹，里面存放了一个使用[`tv.py`](tv.py)的游戏

> 2026年8月25日 11:29:10

- 增加版权声明
- 修改`save`和`load`的类型注解
- 采纳了由`gurew23`提出的[Issue](https://github.com/userwnt/Terminal_Viewer/issues/1) #1
- 移除了`demo`下重复的`tv.py`

> 2026年8月26日 8:53:45

- 修正[`README`](README_zh.md)中的类型注解

> 2026年8月26日 12:45:50

- 移除了帧缓存
- 扩大像素级缓存容量

> 2026年8月27日 13:57:49

- 增加了极其拉跨的睡眠时间补偿，效果感人😭
- 更换了新的demo