import asyncio
from encodings.punycode import T
import win32api
import win32con

PRESS_GAP = 0.005

KEY_OCCUPIED: set[str] = set()

def is_key_pressed(key_code: int) -> bool:
    """
    检测按键是否被按下

    Args:
        key_code (int): 虚拟键码
    """

    return win32api.GetAsyncKeyState(key_code) & 0x8000 != 0


async def hold_key(key: str, duration: float) -> None:
    """
    长按

    Args:
        key (str): note
        duration (float): 持续时间
    """
    vk_code = ord(key.upper())

    while key in KEY_OCCUPIED:  # 等key占用结束
        await asyncio.sleep(0)
    KEY_OCCUPIED.add(key)
    scan_code = win32api.MapVirtualKey(vk_code, 0)
    win32api.keybd_event(vk_code, scan_code, 0, 0)
    await asyncio.sleep(max(duration, PRESS_GAP))  # 保证演奏的连贯性
    # 释放按键
    win32api.keybd_event(vk_code, scan_code, win32con.KEYEVENTF_KEYUP, 0)
    await asyncio.sleep(0.016)
    KEY_OCCUPIED.discard(key)



async def press_key(key: str) -> None:
    """
    短按

    Args:
        key (str): note
    """
    vk_code = ord(key.upper())
    scan_code = win32api.MapVirtualKey(vk_code, 0)
    while key in KEY_OCCUPIED:  # 等key占用结束
        await asyncio.sleep(0)
    KEY_OCCUPIED.add(key)
    win32api.keybd_event(vk_code, scan_code, 0, 0)
    await asyncio.sleep(PRESS_GAP)  # 短暂延迟
    win32api.keybd_event(vk_code, scan_code, win32con.KEYEVENTF_KEYUP, 0)
    await asyncio.sleep(0.016)
    KEY_OCCUPIED.discard(key)

def release_all_key():
    for key in KEY_OCCUPIED:
        vk_code = ord(key.upper())
        scan_code = win32api.MapVirtualKey(vk_code, 0)
        win32api.keybd_event(vk_code, scan_code, win32con.KEYEVENTF_KEYUP, 0)
    KEY_OCCUPIED.clear()