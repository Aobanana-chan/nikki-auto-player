import asyncio
from typing import cast
import pyautogui
from core.melody import BPMNoteData, HoldNoteData, Melody, TapNoteData
from utils import tools
from loguru import logger
from utils.logs import log
from . import press_key as pk
from core import config

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

async def melody_play(notes: list[BPMNoteData | TapNoteData | HoldNoteData]) -> None:
    '''
    播放旋律数据
    '''
    pyautogui.FAILSAFE = True
    log("Action: Playing melody...", level="INFO")
    current_bpm = GLOBAL_BPM
    note_play_task: list[asyncio.Task] = []
    time_offset = 0
    bpm_start_beat = 0

    # 预处理旋律数据
    # pmelody = [tools.process_melody_note(note_tuple) for note_tuple in melody.melody]

    for note in notes:
        match note["type"]:
            case "bpm":
                current_bpm = note["bpm"]
                time_offset += tools.calc_beat_duration(note["beat"] - bpm_start_beat, current_bpm)
                bpm_start_beat = note["beat"]
                async def show_bpm_change_log(sleep_time: float):
                    await asyncio.sleep(sleep_time)
                    log(f"BPM changed to: {current_bpm}", style="cyan", level="INFO")
                note_play_task.append(asyncio.create_task(show_bpm_change_log(time_offset)))
            case "tap":
                delta_time = tools.calc_beat_duration(note["beat"] - bpm_start_beat, current_bpm)
                note_play_task.append(asyncio.create_task(play_single_note(delta_time + time_offset, note["note"])))
            case "hold":
                # 暂时不考虑hold过程中bpm改变的复杂情况
                hold_time = tools.calc_beat_duration(note["end_beat"] - note["beat"], current_bpm)
                start_delta_time = tools.calc_beat_duration(note["beat"] - bpm_start_beat, current_bpm)
                note_play_task.append(asyncio.create_task(play_hold_note(start_delta_time + time_offset, note["note"], hold_time)))

    gather = asyncio.gather(*note_play_task)
    while True:
        if gather.done():
            return
        if pk.is_key_pressed(tools.get_vk_code(config.exit_key)):
            log("演奏已中断", style="bright_yellow", level="INFO")
            gather.cancel()
            return
        await asyncio.sleep(0)

def play_melody_async(melody: Melody):
    loop = asyncio.new_event_loop()
    loop.run_until_complete(melody_play(melody.melody))
