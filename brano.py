import librosa
import matplotlib.pyplot as plt
import numpy as np
np.set_printoptions(threshold=np.inf)
audio_path = "MUEVELOU.mp3"

#1. Upload music
y, sr = librosa.load(audio_path)

#2. Find BPM (average tempo) and beats
tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
tempo_val = float(tempo)
print(f"BPM medio: {tempo_val:.1f}")

beat_times = librosa.frames_to_time(beats, sr=sr)

#3. Calculate RMS power (sound intensity level)
rms = librosa.feature.rms(y=y)[0]
rms = rms / max(rms)  # normalizza tra 0 e 1
frames = range(len(rms))
times = librosa.frames_to_time(frames, sr=sr)

