# ==============================================================================
# 文件路径: music_service.py
# 包含服务: AppleMusicStoreService (C# WinRT SMTC 原生桥接 + 系统全局音量控制)
# ==============================================================================
import ctypes
import json
import subprocess
import threading


class AppleMusicStoreService:
    VK_MEDIA_NEXT = 0xB0
    VK_MEDIA_PREV = 0xB1
    VK_MEDIA_PLAY_PAUSE = 0xB3

    _listener = None
    _is_running = False
    _ps_proc = None

    PS_SMTC_SCRIPT = """
$code = @'
using System;
using System.IO;
using System.Threading.Tasks;
using Windows.Media.Control;
using Windows.Storage.Streams;

public class MediaBridge {
    public static string GetMediaJson() {
        try {
            var mgr = GlobalSystemMediaTransportControlsSessionManager.RequestAsync().GetAwaiter().GetResult();
            if (mgr == null) return "null";
            
            var sessions = mgr.GetSessions();
            GlobalSystemMediaTransportControlsSession target = null;
            foreach (var s in sessions) {
                if (s.SourceAppUserModelId.IndexOf("Apple", StringComparison.OrdinalIgnoreCase) >= 0) {
                    target = s;
                    break;
                }
            }
            if (target == null) target = mgr.GetCurrentSession();
            if (target == null) return "null";

            var prop = target.TryGetMediaPropertiesAsync().GetAwaiter().GetResult();
            var pb = target.GetPlaybackInfo();
            bool isPlaying = (pb != null && pb.PlaybackStatus == GlobalSystemMediaTransportControlsSessionPlaybackStatus.Playing);

            string artB64 = "";
            if (prop != null && prop.Thumbnail != null) {
                try {
                    var streamRef = prop.Thumbnail.OpenReadAsync().GetAwaiter().GetResult();
                    if (streamRef != null && streamRef.Size > 0) {
                        using (var stream = streamRef.AsStreamForRead()) {
                            byte[] buffer = new byte[stream.Length];
                            stream.Read(buffer, 0, buffer.Length);
                            artB64 = Convert.ToBase64String(buffer);
                        }
                    }
                } catch {}
            }

            string title = (prop != null && !string.IsNullOrEmpty(prop.Title)) ? prop.Title : "正在播放";
            string artist = (prop != null && !string.IsNullOrEmpty(prop.Artist)) ? prop.Artist : "Apple Music";
            string album = (prop != null && !string.IsNullOrEmpty(prop.AlbumTitle)) ? prop.AlbumTitle : "";

            title = title.Replace("\"", "\\\"");
            artist = artist.Replace("\"", "\\\"");
            album = album.Replace("\"", "\\\"");

            return "{\\\"connected\\\":true,\\\"is_playing\\\":" + (isPlaying ? "true" : "false") + 
                   ",\\\"title\\\":\\\"" + title + "\\\",\\\"artist\\\":\\\"" + artist + 
                   "\\\",\\\"album\\\":\\\"" + album + "\\\",\\\"artwork\\\":\\\"" + artB64 + "\\\"}";
        } catch {
            return "null";
        }
    }
}
'@
Add-Type -TypeDefinition $code -Language CSharp -IgnoreWarnings
while($true) {
    $res = [MediaBridge]::GetMediaJson()
    Write-Output ("#MEDIA#" + $res)
    Start-Sleep -Milliseconds 1200
}
"""

    @classmethod
    def launch_store_app(cls):
        try:
            subprocess.Popen("explorer.exe shell:AppsFolder\\AppleInc.AppleMusicWin_nzyj5cx40ttqa!App", shell=True)
        except Exception:
            try:
                subprocess.Popen("start applemusic:", shell=True)
            except Exception:
                pass

    @classmethod
    def toggle_play(cls):
        ctypes.windll.user32.keybd_event(cls.VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
        ctypes.windll.user32.keybd_event(cls.VK_MEDIA_PLAY_PAUSE, 0, 2, 0)

    @classmethod
    def next_track(cls):
        ctypes.windll.user32.keybd_event(cls.VK_MEDIA_NEXT, 0, 0, 0)
        ctypes.windll.user32.keybd_event(cls.VK_MEDIA_NEXT, 0, 2, 0)

    @classmethod
    def prev_track(cls):
        ctypes.windll.user32.keybd_event(cls.VK_MEDIA_PREV, 0, 0, 0)
        ctypes.windll.user32.keybd_event(cls.VK_MEDIA_PREV, 0, 2, 0)

    @classmethod
    def set_system_volume(cls, percent):
        vol = max(0, min(100, int(percent)))
        ps_cmd = (
            f"(New-Object -ComObject WScript.Shell).SendKeys([char]174 * 50); "
            f"(New-Object -ComObject WScript.Shell).SendKeys([char]175 * {int(vol / 2)})"
        )
        threading.Thread(
            target=lambda: subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd], creationflags=subprocess.CREATE_NO_WINDOW
            ),
            daemon=True
        ).start()

    @classmethod
    def set_state_listener(cls, callback):
        cls._listener = callback
        if not cls._is_running:
            cls._is_running = True
            threading.Thread(target=cls._stream_reader_worker, daemon=True).start()

    @classmethod
    def _stream_reader_worker(cls):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0

        try:
            cls._ps_proc = subprocess.Popen(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", cls.PS_SMTC_SCRIPT],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            for line in cls._ps_proc.stdout:
                line = line.strip()
                if "#MEDIA#" in line:
                    json_str = line.split("#MEDIA#")[1].strip()
                    if json_str == "null":
                        if cls._listener:
                            cls._listener({
                                "connected": False,
                                "is_playing": False,
                                "title": "未检测到 Apple Music 播放会话",
                                "artist": "点击右侧【唤起 Apple Music】启动客户端并播放歌曲",
                                "album": "",
                                "artwork": ""
                            })
                    else:
                        try:
                            data = json.loads(json_str)
                            if cls._listener:
                                cls._listener(data)
                        except Exception:
                            pass
        except Exception:
            pass