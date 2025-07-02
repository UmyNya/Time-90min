import asyncio
from winsdk.windows.media.control import \
    GlobalSystemMediaTransportControlsSessionManager as MediaManager
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus


async def get_media_status():
    sessions = await MediaManager.request_async()
    current_session = sessions.get_current_session()
    if current_session:
        playback_info = current_session.get_playback_info()
        status = playback_info.playback_status
        status_mapping = {
            PlaybackStatus.CLOSED: "关闭",
            PlaybackStatus.PAUSED: "暂停",
            PlaybackStatus.PLAYING: "播放",
            PlaybackStatus.STOPPED: "停止",
            PlaybackStatus.CHANGING: "转变状态"
        }
        return status_mapping.get(status, "未知状态")
    return "无活动媒体会话"


async def toggle_media_playback():
    """暂停或播放当前媒体"""
    sessions = await MediaManager.request_async()
    current_session = sessions.get_current_session()
    if current_session:
        playback_info = current_session.get_playback_info()
        status = playback_info.playback_status
        
        if status == PlaybackStatus.PLAYING:
            # 如果正在播放，则暂停
            await current_session.try_pause_async()
            return "已暂停媒体"
        elif status == PlaybackStatus.PAUSED:
            # 如果已暂停，则播放
            await current_session.try_play_async()
            return "已恢复播放"
        else:
            return f"当前媒体状态为 {status}，无法切换播放状态"
    return "无活动媒体会话"


if __name__ == "__main__":
    try:
        # 获取当前媒体状态
        status = asyncio.run(get_media_status())
        print(f"当前系统媒体状态: {status}")
        
        # 如果有参数，则尝试切换媒体播放状态
        import sys
        if len(sys.argv) > 1 and sys.argv[1] == "--toggle":
            result = asyncio.run(toggle_media_playback())
            print(result)
            # 切换后再次获取状态
            status = asyncio.run(get_media_status())
            print(f"切换后媒体状态: {status}")
    except Exception as e:
        print(f"发生错误: {e}")
    