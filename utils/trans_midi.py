import mido
import json
from collections import defaultdict

def midi_note_to_solfege(note: int) -> str | None:
    """
    将MIDI音符编号转换为C大调唱名系统
    """
    # 计算八度偏移
    octave_offset = (note // 12) - 4
    
    # C大调唱名映射
    base_notes = {
        0: "do",   # C
        2: "re",   # D
        4: "mi",   # E
        5: "fa",   # F
        7: "so",   # G
        9: "la",   # A
        11: "ti"   # B
    }
    
    # 计算音符在C大调中的名称
    note_index = note % 12
    if note_index in base_notes:
        base_name = base_notes[note_index]
    else:
        return None
    
    # 根据八度偏移添加后缀
    if octave_offset == 0:  # 低八度
        return base_name + '/'
    elif octave_offset == 1:  # 中音
        return base_name
    elif octave_offset == 2:  # 高八度
        return base_name + '#'
    else:
        return None

def midi_to_json(midi_file_path, output_json_path):
    # 加载MIDI文件
    mid = mido.MidiFile(midi_file_path)
    
    # 基本文件信息
    ticks_per_beat = mid.ticks_per_beat
    threshold_ticks = ticks_per_beat // 64  # 1/64拍的ticks阈值
    
    # 音符过滤范围 - C4到B6
    NOTE_MIN = 60   # C4
    NOTE_MAX = 95   # B6
    
    # 存储结果事件
    events = []
    # 记录当前活动的音符
    active_notes = defaultdict(list)
    # 记录最后的活动时间
    last_absolute_time = 0
    # 当前BPM (默认120bpm)
    current_bpm = 120.0
    
    # 辅助函数：ticks转beat
    def ticks_to_beat(ticks):
        return round(ticks / ticks_per_beat, 4)
    
    # 处理BPM变化（通常在第0轨）
    for track in mid.tracks:
        abs_time = 0
        for msg in track:
            abs_time += msg.time
            if msg.type == 'set_tempo':
                # 计算BPM值
                bpm = round(60000000 / msg.tempo, 1)
                beat = ticks_to_beat(abs_time)
                events.append({
                    "type": "bpm",
                    "beat": beat,
                    "bpm": bpm
                })
                current_bpm = bpm

    # 处理音符事件
    for track_idx, track in enumerate(mid.tracks):
        abs_time = 0  # 轨道的绝对时间（ticks）
        
        for msg in track:
            abs_time += msg.time
            last_absolute_time = max(last_absolute_time, abs_time)
            current_beat = ticks_to_beat(abs_time)
            
            # 音符按下事件
            if msg.type == 'note_on' and msg.velocity > 0 and NOTE_MIN <= msg.note <= NOTE_MAX:
                # 截断相同音符重叠的部分
                if msg.note in active_notes:
                    # 查找所有相同音符的活动音符
                    for note_info in active_notes[msg.note][:]:
                        # 检查新音符开始时间是否在已有音符结束时间之前（重叠）
                        if note_info['end_beat'] is None or current_beat < note_info['end_beat']:
                            # 截断现有音符
                            note_info['end_beat'] = current_beat
                            # 生成截断音符事件
                            if note_solfege := midi_note_to_solfege(msg.note):
                                events.append({
                                    "type": "hold",
                                    "beat": note_info['start_beat'],
                                    "note": note_solfege,
                                    "end_beat": current_beat
                                })
                            active_notes[msg.note].remove(note_info)
                
                # 记录新音符开始
                active_notes[msg.note].append({
                    'start_tick': abs_time,
                    'start_beat': current_beat,
                    'end_beat': None,  # 初始没有结束时间
                    'track': track_idx
                })
            
            # 音符释放事件（包括velocity=0的note_on）
            if (msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0)) and NOTE_MIN <= msg.note <= NOTE_MAX:
                if msg.note not in active_notes or not active_notes[msg.note]:
                    continue  # 没有对应开始事件
                
                # 处理时间最早的活动音符
                active_note = active_notes[msg.note].pop(0)
                
                duration = abs_time - active_note['start_tick']
                start_beat = active_note['start_beat']
                end_beat = current_beat
                
                # 判断是tap还是hold
                if note_solfege := midi_note_to_solfege(msg.note):
                    if duration > threshold_ticks:
                        events.append({
                            "type": "hold",
                            "beat": start_beat,
                            "note": note_solfege,
                            "end_beat": end_beat
                        })
                    else:
                        events.append({
                            "type": "tap",
                            "beat": start_beat,
                            "note": note_solfege
                        })

    # 处理没有对应note_off的音符（在文件结束时）
    final_beat = ticks_to_beat(last_absolute_time)
    for note, active_list in active_notes.items():
        for active_note in active_list:
            if active_note['end_beat'] is None:
                if note_solfege := midi_note_to_solfege(msg.note):
                    events.append({
                        "type": "hold",
                        "beat": active_note['start_beat'],
                        "note": note,
                        "end_beat": final_beat
                    })

    # 按事件发生时间排序
    events.sort(key=lambda x: x['beat'])
    
    file_data = {
        "nikki_player_version": "1.0",
        "instrument": "violin",
        "music_name": "春日影",
        "melody": events
    }
    # 保存为JSON文件（每行一个事件）
    with open(output_json_path, 'w') as f:
        f.write(json.dumps(file_data))
    
    return events

# 计算时间间隔的辅助函数
def calculate_time_interval(delta_beat, bpm):
    """
    根据节拍差和BPM计算时间间隔
    
    参数:
    delta_beat (float): 两个事件之间的节拍差值
    bpm (float): 当前节拍速度（每分钟节拍数）
    
    返回:
    float: 以秒为单位的时间间隔
    """
    # 计算每拍的时间（秒）
    seconds_per_beat = 60.0 / bpm
    
    # 计算整个间隔的时间
    time_interval = delta_beat * seconds_per_beat
    
    return round(time_interval, 4)

# 使用示例
if __name__ == "__main__":
    input_midi = "harukikake.mid"   # 输入MIDI文件路径
    output_json = "harukikake.json" # 输出JSON文件路径
    
    # 转换MIDI文件
    events = midi_to_json(input_midi, output_json)
    print(f"转换完成! 共生成 {len(events)} 个事件")
    print(f"结果已保存至: {output_json}")