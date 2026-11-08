import os
import math
import wave
import struct
import numpy as np

SAMPLE_RATE = 44100

def save_wav(filename: str, samples: np.ndarray, sample_rate: int = SAMPLE_RATE):
    """Save 1D float array (-1.0 to 1.0) as 16-bit mono WAV file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    # Clip and convert to 16-bit signed PCM
    clipped = np.clip(samples, -0.98, 0.98)
    int_samples = (clipped * 32767).astype(np.int16)
    
    with wave.open(filename, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int_samples.tobytes())

def generate_tone(freq: float, duration: float, wave_type: str = 'sine', sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Generate tone array with specified waveform."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    if wave_type == 'sine':
        return np.sin(2 * np.pi * freq * t)
    elif wave_type == 'triangle':
        return 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1
    elif wave_type == 'square':
        return np.sign(np.sin(2 * np.pi * freq * t))
    elif wave_type == 'saw':
        return 2 * (t * freq - np.floor(t * freq + 0.5))
    return np.sin(2 * np.pi * freq * t)

def synth_title_theme(output_path: str):
    """Synthesize noir synth loop (~10s) with minor progression."""
    duration = 8.0
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    audio = np.zeros_like(t)
    
    # Chords: Dm (D3, F3, A3), Bb (Bb2, D3, F3), Gm (G2, Bb2, D3), A7 (A2, C#3, E3, G3)
    chords = [
        [146.83, 174.61, 220.00],        # Dm
        [116.54, 146.83, 174.61],        # Bb
        [98.00, 116.54, 146.83],         # Gm
        [110.00, 138.59, 164.81, 196.00] # A7
    ]
    chord_len = duration / len(chords)
    
    for i, chord in enumerate(chords):
        idx_start = int(i * chord_len * SAMPLE_RATE)
        idx_end = int((i + 1) * chord_len * SAMPLE_RATE)
        seg_len = (idx_end - idx_start) / SAMPLE_RATE
        seg_t = np.linspace(0, seg_len, idx_end - idx_start, endpoint=False)
        
        # Envelope: soft attack and release
        env = np.sin(np.pi * np.linspace(0, 1, len(seg_t))) ** 0.5
        
        seg_audio = np.zeros_like(seg_t)
        for freq in chord:
            # Subtle detuning and warmth with warm triangle + sine
            seg_audio += 0.25 * np.sin(2 * np.pi * freq * seg_t)
            seg_audio += 0.15 * (2 * np.abs(2 * (seg_t * freq - np.floor(seg_t * freq + 0.5))) - 1)
            # Low octave drone
            seg_audio += 0.18 * np.sin(2 * np.pi * (freq / 2.0) * seg_t)
            
        audio[idx_start:idx_end] += seg_audio * env
        
    # Add gentle noir vibrato / LFO
    lfo = 1.0 + 0.05 * np.sin(2 * np.pi * 3.5 * t)
    audio = audio * lfo
    save_wav(output_path, audio)

def synth_interrogation_theme(output_path: str):
    """Synthesize tense low drone with a mechanical clock ticking pulse (~8s loop)."""
    duration = 8.0
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    audio = np.zeros_like(t)
    
    # Low ominous drone: 65.41 Hz (C2) with slow 0.2Hz modulation
    drone = 0.4 * np.sin(2 * np.pi * 65.41 * t) + 0.2 * np.sin(2 * np.pi * 98.0 * t) # C2 + G2
    mod = 0.8 + 0.2 * np.sin(2 * np.pi * 0.25 * t)
    audio += drone * mod
    
    # Ticking pulse every 0.5 seconds
    ticks = np.arange(0, duration, 0.5)
    for tick_time in ticks:
        tick_idx = int(tick_time * SAMPLE_RATE)
        tick_len = int(0.04 * SAMPLE_RATE) # 40ms click
        if tick_idx + tick_len < len(audio):
            tt = np.linspace(0, 0.04, tick_len, endpoint=False)
            decay = np.exp(-tt * 150)
            # High crisp click (alternating tick / tock frequencies)
            f_tick = 1800 if int(tick_time * 2) % 2 == 0 else 1200
            click = 0.25 * np.sin(2 * np.pi * f_tick * tt) * decay
            audio[tick_idx:tick_idx + tick_len] += click
            
    save_wav(output_path, audio)

def synth_win_sting(output_path: str):
    """Triumphant sting: C -> E -> G -> C major brass fanfare."""
    notes = [(261.63, 0.2), (329.63, 0.2), (392.00, 0.2), (523.25, 1.2)]
    total_len = sum(d for _, d in notes)
    audio = []
    for freq, dur in notes:
        t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
        env = np.exp(-t * (1.5 if dur > 0.5 else 0.5))
        # Fanfare brass (harmonics)
        tone = 0.5 * np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * (2 * freq) * t) + 0.15 * np.sin(2 * np.pi * (3 * freq) * t)
        audio.append(tone * env)
    save_wav(output_path, np.concatenate(audio))

def synth_lose_sting(output_path: str):
    """Sad trombone sting: descending slide D -> Db -> C -> low B with vibrato."""
    notes = [(293.66, 0.4), (277.18, 0.4), (261.63, 0.4), (233.08, 1.0)]
    audio = []
    for i, (freq, dur) in enumerate(notes):
        t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
        vibrato = 1.0 + (0.04 * np.sin(2 * np.pi * 5 * t) if i == len(notes) - 1 else 0.0)
        env = np.exp(-t * (2.0 if i < 3 else 1.2))
        tone = 0.5 * np.sin(2 * np.pi * freq * vibrato * t) + 0.3 * (2 * (t * freq - np.floor(t * freq + 0.5)))
        audio.append(tone * env)
    save_wav(output_path, np.concatenate(audio))

def synth_key_click(output_path: str):
    """Typewriter/keyboard click: 15ms snappy click."""
    duration = 0.015
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    noise = np.random.uniform(-1, 1, len(t))
    decay = np.exp(-t * 350)
    audio = 0.15 * noise * decay + 0.15 * np.sin(2 * np.pi * 2400 * t) * decay
    save_wav(output_path, audio)

def synth_token_spent(output_path: str):
    """Token spent SFX: 120ms two-tone metallic chime."""
    t1 = np.linspace(0, 0.06, int(SAMPLE_RATE * 0.06), endpoint=False)
    t2 = np.linspace(0, 0.10, int(SAMPLE_RATE * 0.10), endpoint=False)
    s1 = 0.3 * np.sin(2 * np.pi * 880 * t1) * np.exp(-t1 * 40)
    s2 = 0.35 * np.sin(2 * np.pi * 440 * t2) * np.exp(-t2 * 25)
    save_wav(output_path, np.concatenate([s1, s2]))

def synth_accuse_stamp(output_path: str):
    """Accuse stamp: heavy dramatic gavel impact with low thump and resonance."""
    duration = 0.45
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    # Heavy low impact thump
    impact = 0.6 * np.sin(2 * np.pi * (120 * np.exp(-t * 20)) * t) * np.exp(-t * 12)
    wood_knock = 0.3 * np.sin(2 * np.pi * 380 * t) * np.exp(-t * 25)
    audio = impact + wood_knock
    save_wav(output_path, audio)

def synth_suspect_nervous(output_path: str):
    """Suspect nervous cue: 350ms fluttering dissonant trill."""
    duration = 0.35
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    tremolo = 0.5 + 0.5 * np.sin(2 * np.pi * 18 * t)
    # Dissonant tritone (600 Hz and 850 Hz)
    tone = 0.25 * np.sin(2 * np.pi * 600 * t) + 0.25 * np.sin(2 * np.pi * 848.5 * t)
    env = np.sin(np.pi * (t / duration)) ** 0.5
    audio = tone * tremolo * env
    save_wav(output_path, audio)

def ensure_all_audio_assets(assets_dir: str):
    """Generate all missing audio files programmatically."""
    os.makedirs(assets_dir, exist_ok=True)
    mapping = {
        "title.wav": synth_title_theme,
        "interrogation.wav": synth_interrogation_theme,
        "win.wav": synth_win_sting,
        "lose.wav": synth_lose_sting,
        "key_click.wav": synth_key_click,
        "token_spent.wav": synth_token_spent,
        "accuse_stamp.wav": synth_accuse_stamp,
        "suspect_nervous.wav": synth_suspect_nervous,
    }
    for filename, synth_fn in mapping.items():
        file_path = os.path.join(assets_dir, filename)
        if not os.path.exists(file_path):
            synth_fn(file_path)

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "assets/audio"
    ensure_all_audio_assets(target)
    print("All audio files generated in", target)
