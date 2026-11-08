import os
from typing import Optional
from alibi.audio.synthesizer import ensure_all_audio_assets

class AudioManager:
    """Manages audio playback using pygame.mixer with safe fallback for headless environments."""
    
    _instance: Optional['AudioManager'] = None
    
    def __init__(self, assets_dir: str = "assets/audio"):
        self.assets_dir = assets_dir
        self.available = False
        self.muted = False
        self.music_volume = 0.75
        self.sfx_volume = 0.75
        self.current_music: Optional[str] = None
        self._sfx_cache = {}
        
        # Ensure files exist
        try:
            ensure_all_audio_assets(self.assets_dir)
        except Exception:
            pass
            
        # Initialize pygame.mixer safely
        try:
            import pygame
            # Don't show pygame welcome msg if possible
            os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.available = True
        except Exception:
            self.available = False
            
    @classmethod
    def get_instance(cls, assets_dir: str = "assets/audio") -> 'AudioManager':
        if cls._instance is None:
            cls._instance = AudioManager(assets_dir)
        return cls._instance

    def play_music(self, track_name: str, loop: bool = True):
        """Play looping or one-shot background music track."""
        if not self.available or self.muted:
            return
            
        file_path = os.path.join(self.assets_dir, f"{track_name}.wav")
        if not os.path.exists(file_path):
            return
            
        try:
            import pygame
            if self.current_music == track_name and pygame.mixer.music.get_busy():
                return
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.set_volume(0.0 if self.muted else self.music_volume)
            pygame.mixer.music.play(-1 if loop else 0)
            self.current_music = track_name
        except Exception:
            pass

    def stop_music(self):
        """Stop background music."""
        if not self.available:
            return
        try:
            import pygame
            pygame.mixer.music.stop()
            self.current_music = None
        except Exception:
            pass

    def play_sfx(self, sfx_name: str):
        """Play short sound effect."""
        if not self.available or self.muted:
            return
            
        file_path = os.path.join(self.assets_dir, f"{sfx_name}.wav")
        if not os.path.exists(file_path):
            return
            
        try:
            import pygame
            if sfx_name not in self._sfx_cache:
                self._sfx_cache[sfx_name] = pygame.mixer.Sound(file_path)
            sound = self._sfx_cache[sfx_name]
            sound.set_volume(self.sfx_volume)
            sound.play()
        except Exception:
            pass

    def toggle_mute(self) -> bool:
        """Toggle mute state on or off."""
        self.muted = not self.muted
        if self.available:
            try:
                import pygame
                pygame.mixer.music.set_volume(0.0 if self.muted else self.music_volume)
            except Exception:
                pass
        return self.muted

    def set_music_volume(self, volume: float):
        self.music_volume = max(0.0, min(1.0, volume))
        if self.available and not self.muted:
            try:
                import pygame
                pygame.mixer.music.set_volume(self.music_volume)
            except Exception:
                pass

    def set_sfx_volume(self, volume: float):
        self.sfx_volume = max(0.0, min(1.0, volume))
        for sound in self._sfx_cache.values():
            try:
                sound.set_volume(self.sfx_volume)
            except Exception:
                pass
