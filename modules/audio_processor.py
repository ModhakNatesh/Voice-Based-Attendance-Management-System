"""Audio processing module for voice attendance system."""
import os
import wave
import pyaudio
import noisereduce as nr
import librosa
import numpy as np
import soundfile as sf
from datetime import datetime
from modules.utils import CONFIG, logger
from modules.db_manager import log_event

# Audio recording parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 5  # Duration per sample

def ensure_directories():
    """Creates necessary directories if they don't exist."""
    os.makedirs(CONFIG["audio_folder"], exist_ok=True)
    os.makedirs(CONFIG["attendance_temp"], exist_ok=True)

def validate_sample(audio_path):
    """Checks if the recorded sample meets quality standards."""
    try:
        y, sr = librosa.load(audio_path, sr=None)
        
        # Check energy (avoid silent/too quiet samples)
        energy = np.sum(y**2) / len(y)
        if energy < CONFIG.get("min_energy_threshold", 0.003):
            raise ValueError("Sample energy too low (silent/quiet)")
            
        # Check duration
        duration = librosa.get_duration(y=y, sr=sr)
        if duration < 4.5:  # At least 4.5 seconds of usable audio
            raise ValueError("Sample too short")
            
        return True
    except Exception as e:
        log_event("ERROR", f"Invalid sample {audio_path}: {str(e)}")
        if os.path.exists(audio_path):
            os.remove(audio_path)  # Delete corrupted/low-quality sample
        return False

def record_single_sample(filepath):
    """Records one high-quality voice sample."""
    p = pyaudio.PyAudio()
    stream = None
    try:
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        
        logger.info(f"Recording sample to {filepath}")
        print("\n🎤 Recording... Please speak naturally.")
        
        frames = []
        for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            frames.append(stream.read(CHUNK))
        
        # Save raw recording
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
        
        # Apply noise reduction
        y, sr = librosa.load(filepath, sr=None)
        y_clean = nr.reduce_noise(y=y, sr=sr)
        sf.write(filepath, y_clean, sr)
        
        # Validate sample quality
        if not validate_sample(filepath):
            raise ValueError(f"Sample failed quality check")
            
        return True
        
    except Exception as e:
        logger.error(f"Recording error: {str(e)}")
        if os.path.exists(filepath):
            os.remove(filepath)
        return False
    finally:
        if stream:
            stream.stop_stream()
            stream.close()
        p.terminate()

def record_voice_samples(student_name, user_id):
    """Records 3 validated samples."""
    ensure_directories()
    samples = []
    
    for i in range(1, 4):
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            filepath = os.path.join(
                CONFIG["audio_folder"],
                f"{user_id}_{student_name}_{i}.wav"
            )
            try:
                print(f"\n🎤 Recording sample {i}/3... (Speak naturally)")
                if record_single_sample(filepath):
                    samples.append(filepath)
                    logger.info(f"Successfully recorded sample {i} for {user_id}")
                    break
                else:
                    retry_count += 1
                    print(f"⚠️ Sample quality check failed. Retry {retry_count}/{max_retries}")
            except Exception as e:
                retry_count += 1
                print(f"⚠️ Recording failed: {str(e)}")
                print(f"Retry {retry_count}/{max_retries}")
        
        if retry_count >= max_retries:
            raise ValueError(f"Failed to record sample {i} after {max_retries} attempts")
    
    if len(samples) < 3:
        raise ValueError("Failed to collect all required voice samples")
    
    return samples

def record_attendance_sample():
    """Records a single sample for attendance marking."""
    ensure_directories()
    temp_file = os.path.join(CONFIG["attendance_temp"], f"attendance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav")
    
    try:
        print("\nSpeak now for attendance verification...")
        if record_single_sample(temp_file):
            return temp_file
        return None
    except Exception as e:
        logger.error(f"Attendance recording failed: {str(e)}")
        return None