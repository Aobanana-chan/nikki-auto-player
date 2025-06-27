import asyncio
import time
from typing import cast
import pyautogui
from utils import tools
from loguru import logger
from utils.logs import log
from . import press_key as pk
from core import config, Melody

GLOBAL_BPM = config.global_bpm

async def play_single_note(sleep_time: float, note: str):
    await asyncio.sleep(sleep_time)
    try:
        key = cast(str, config.key_mapping[str(note)]).lower()
    except KeyError:
        log(f"Unknown note: {note}, skipped.", style="yellow", level="WARNING")
        return
    await pk.press_key(key)
    log(f"Notes: {' '.join(note)}", style="cyan", level="DEBUG")


async def play_hold_note(sleep_time: float, note: str, duration: float):
    await asyncio.sleep(sleep_time)
    try:
        key = cast(str, config.key_mapping[str(note)]).lower()
    except KeyError:
        log(f"Unknown note: {note}, skipped.", style="yellow", level="WARNING")
        return
    await pk.hold_key(key, duration)
    log(f"Notes: {' '.join(note)}", style="cyan", level="DEBUG")

async def melody_play(melody: Melody) -> None:
    '''
    播放旋律数据
    '''
    pyautogui.FAILSAFE = True
    log("Action: Playing melody...", level="INFO")
    next_note_time = time.time()
    cur_notes = []  # this section's notes
    current_bpm = melody.bpm
    current_timeSignature = "4/4"
    note_play_task: list[asyncio.Task] = []
    time_offset = 0

    # 预处理旋律数据
    pmelody = [tools.process_melody_note(note_tuple) for note_tuple in melody.melody]

    for i, (note, beat_value) in enumerate(pmelody):
        # check if exit
        # if pk.is_key_pressed(tools.get_vk_code(config.exit_key)):
        #     log("演奏已中断", style="bright_yellow", level="INFO")
        #     return

        cur_time = time.time()
        # if cur_time < next_note_time:
        #     time.sleep(next_note_time - cur_time)

        if note == 'bpm':
            try:
                current_bpm = float(beat_value)
                log(f"BPM changed to: {current_bpm}", style="cyan", level="INFO")
                continue
            except (ValueError, TypeError):
                log(f"Invalid BPM value: {beat_value}", style="red", level="ERROR")
                continue

        if note == "timeSig":
            try:
                current_timeSignature = beat_value
                log(f"Time signature changed to: {current_timeSignature}", style="cyan", level="INFO")
                continue
            except Exception:
                log(f"Invalid time signature value: {beat_value}", style="red", level="ERROR")
                continue

        # 遇到新的Section时，先输出之前收集的音符
        if note == '@@':
            if cur_notes:
                log(f"Notes: {' '.join(cur_notes)}", style="yellow", level="DEBUG")
                cur_notes = []

            log(f"cur section {beat_value} (BPM: {current_bpm})", style="bright_blue", level="INFO")
            continue

        try:
            # 使用当前BPM计算时值
            duration = tools.calculate_duration(beat_value, current_bpm, current_timeSignature)

            # 休止符
            if str(note) == '0':
                cur_notes.append('0')
                # time.sleep(duration * 0.97)

            else:
                # try:
                #     key = config.key_mapping[str(note)].lower()
                #     cur_notes.append(str(note))
                # except KeyError:
                #     log(f"Unknown note: {note}, skipped.", style="yellow", level="WARNING")
                #     continue

                # 长按/短按
                if duration >= config.hold_threshold:
                    # pk.hold_key(key, duration)
                    note_play_task.append(asyncio.create_task(play_hold_note(time_offset, str(note), duration)))
                else:
                    note_play_task.append(asyncio.create_task(play_single_note(time_offset, str(note))))
                    # pk.press_key(key)
                    # await asyncio.sleep(duration * 0.92)
            time_offset += duration

            next_note_time = cur_time + duration
            # time.sleep(min(0.01, duration * 0.05))

        except ValueError:
            log(f"Invalid value: {beat_value}, Skipped", style="red", level="ERROR")
            continue
        except Exception as e:
            log(f"Fault: {note} {beat_value}, Skipped", style="red", level="ERROR")
            logger.error(f"err: {str(e)}")
            continue

    gather = asyncio.gather(*note_play_task)
    while True:
        if gather.done():
            return
        if pk.is_key_pressed(tools.get_vk_code(config.exit_key)):
            log("演奏已中断", style="bright_yellow", level="INFO")
            return
        await asyncio.sleep(0)

def play_melody_async(melody: Melody):
    loop = asyncio.new_event_loop()
    loop.run_until_complete(melody_play(melody))
