## Overview

这个程序是通过加载`{score}.json`的信息来演奏的，其字段包括

- `version`: **Nikki Auto Player** 的版本
- `instrument`: **乐器名**（目前只写了 violin）
- `music_name`: **乐谱名**
- `melody`: **旋律数据**

e.g. (先别太关注melody是什么鬼，其编写格式稍后会介绍到)
```json
{
    "version": "1.0",
    "instrument": "violin",
    "music_name": "千本樱",
    "melody": [
        {
            "type": "bpm",
            "beat": 0.0,
            "bpm": 150.0
        },
        {
            "type": "hold",
            "beat": 0.0,
            "note": "so/",
            "end_beat": 2.9896
        },
    ]
}
```
## 编写你的谱子

### 使用脚本将midi文件转为谱面
推荐的谱面编写方式，通过fl studio或cubase等软件编写谱面，输出midi
将midi文件放入midi文件夹中，然后执行utils/trans_midi.py脚本，谱面会自动生成在score文件夹
处理程序只会处理C4-B6之间的白键

### 谱面格式
melody字段的格式为这几种note

{"type": "bpm", "beat": 具体在哪一拍改变bpm,"bpm": 改变bpm的值}
{"type": "tap", "beat": 具体在哪一拍单击, "note": 具体的音符}
{"type": "hold", "beat": 具体在哪一拍开始长按, "note": 具体的音符, "end_beat": 具体在哪一拍结束长按}

TODO 更详细的说明 ...