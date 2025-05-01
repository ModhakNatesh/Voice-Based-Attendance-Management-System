"""Voice processing module for attendance system."""
import os
import pickle
import numpy as np
import librosa
from resemblyzer import VoiceEncoder, preprocess_wav
from modules.utils import CONFIG, logger
from modules.db_manager import log_event

def detect_spoofing(audio_path):
    """Checks if audio is live (not a recording)."""
    try:
        y, sr = librosa.load(audio_path)
        energy = np.sum(y**2) / len(y)
        return energy > CONFIG.get("min_energy_threshold", 0.0003)
    except Exception as e:
        logger.error(f"Spoofing detection error: {str(e)}")
        return False

def extract_features(audio_path):
    """Extracts voice embeddings with spoofing check."""
    if not detect_spoofing(audio_path):
        logger.warning(f"Possible spoofing detected for {audio_path}")
        return None
    
    try:
        encoder = VoiceEncoder()
        wav = preprocess_wav(audio_path)
        return encoder.embed_utterance(wav)
    except Exception as e:
        logger.error(f"Feature extraction error: {str(e)}")
        return None

def generate_speaker_embeddings():
    """Averages embeddings from 3 samples per student."""
    encoder = VoiceEncoder()
    embeddings = {}
    
    try:
        # Group samples by student
        student_samples = {}
        for file in os.listdir(CONFIG["audio_folder"]):
            if file.endswith(".wav"):
                parts = file.split("_")
                if len(parts) < 3:
                    continue
                user_id, name = parts[0], parts[1]
                key = (user_id, name)
                student_samples.setdefault(key, []).append(
                    os.path.join(CONFIG["audio_folder"], file)
                )
        
        # Process each student's 3 samples
        for (user_id, name), samples in student_samples.items():
            if len(samples) < 3:
                logger.warning(f"Skipping {name} (ID: {user_id}): Insufficient samples.")
                continue
            
            sample_embeddings = []
            for sample_path in samples:
                try:
                    wav = preprocess_wav(sample_path)
                    embedding = encoder.embed_utterance(wav)
                    sample_embeddings.append(embedding)
                except Exception as e:
                    logger.error(f"Error processing {sample_path}: {str(e)}")
            
            if sample_embeddings:
                embeddings[(user_id, name)] = np.mean(sample_embeddings, axis=0)
        
        # Save embeddings
        with open(CONFIG["speaker_embeddings"], "wb") as f:
            pickle.dump(embeddings, f)
        
        logger.info(f"Generated embeddings for {len(embeddings)} students.")
        return True
        
    except Exception as e:
        logger.error(f"Critical error in generate_speaker_embeddings(): {str(e)}")
        return False

def identify_speaker(audio_path):
    """Identifies a speaker from a voice sample."""
    try:
        # Check if embeddings file exists
        if not os.path.exists(CONFIG["speaker_embeddings"]):
            logger.error("Speaker embeddings file not found")
            return None, 0.0
        
        # Load embeddings
        with open(CONFIG["speaker_embeddings"], "rb") as f:
            embeddings = pickle.load(f)
        
        if not embeddings:
            logger.error("No speaker embeddings found")
            return None, 0.0
        
        # Extract features from sample
        sample_embedding = extract_features(audio_path)
        if sample_embedding is None:
            logger.error("Failed to extract features from sample")
            return None, 0.0
        
        # Find best match
        best_match = None
        best_score = 0.0
        threshold = CONFIG.get("default_similarity_threshold", 0.75)
        
        for (user_id, name), embedding in embeddings.items():
            # Calculate cosine similarity
            similarity = np.dot(sample_embedding, embedding) / (
                np.linalg.norm(sample_embedding) * np.linalg.norm(embedding)
            )
            
            if similarity > best_score:
                best_score = similarity
                best_match = (user_id, name)
        
        logger.info(f"Best match: {best_match}, Score: {best_score:.3f}, Threshold: {threshold}")
        
        if best_score >= threshold:
            return best_match, best_score
        else:
            return None, best_score
            
    except Exception as e:
        logger.error(f"Speaker identification error: {str(e)}")
        return None, 0.0