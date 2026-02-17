import pyaudio
import numpy as np
import scipy.signal
import discord

class AudioHandler(discord.AudioSource):
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.gain = 1.0
        self.pitch_factor = 1.0 # 1.0 = normal, 0.5 = deep, 2.0 = chipmunk
        
        # EQ Gains (dB)
        self.eq_low_db = 0.0
        self.eq_mid_db = 0.0
        self.eq_high_db = 0.0
        
        self.stream = None
        self.CHUNK = 960 # 20ms at 48kHz
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2
        self.RATE = 48000
        self.frames_count = 0
        
        self.sos_cache = None
        self.start_stream()

    def _design_low_shelf(self, cutoff, gain_db, fs=48000, Q=0.707):
        A = 10**(gain_db/40.0)
        w0 = 2 * np.pi * cutoff / fs
        alpha = np.sin(w0) / (2 * Q)
        cos_w0 = np.cos(w0)
        
        b0 =    A * ((A+1) - (A-1)*cos_w0 + 2*np.sqrt(A)*alpha)
        b1 =  2*A * ((A-1) - (A+1)*cos_w0)
        b2 =    A * ((A+1) - (A-1)*cos_w0 - 2*np.sqrt(A)*alpha)
        a0 =        (A+1) + (A-1)*cos_w0 + 2*np.sqrt(A)*alpha
        a1 =   -2 * ((A-1) + (A+1)*cos_w0)
        a2 =        (A+1) + (A-1)*cos_w0 - 2*np.sqrt(A)*alpha
        
        return np.array([b0, b1, b2, a0, a1, a2]) / a0

    def _design_high_shelf(self, cutoff, gain_db, fs=48000, Q=0.707):
        A = 10**(gain_db/40.0)
        w0 = 2 * np.pi * cutoff / fs
        alpha = np.sin(w0) / (2 * Q)
        cos_w0 = np.cos(w0)

        b0 =    A * ((A+1) + (A-1)*cos_w0 + 2*np.sqrt(A)*alpha)
        b1 = -2*A * ((A-1) + (A+1)*cos_w0)
        b2 =    A * ((A+1) + (A-1)*cos_w0 - 2*np.sqrt(A)*alpha)
        a0 =        (A+1) - (A-1)*cos_w0 + 2*np.sqrt(A)*alpha
        a1 =    2 * ((A-1) - (A+1)*cos_w0)
        a2 =        (A+1) - (A-1)*cos_w0 - 2*np.sqrt(A)*alpha

        return np.array([b0, b1, b2, a0, a1, a2]) / a0

    def _design_peaking(self, cutoff, gain_db, fs=48000, Q=1.0):
        A = 10**(gain_db/40.0)
        w0 = 2 * np.pi * cutoff / fs
        alpha = np.sin(w0) / (2 * Q)
        cos_w0 = np.cos(w0)

        b0 =   1 + alpha*A
        b1 =  -2*cos_w0
        b2 =   1 - alpha*A
        a0 =   1 + alpha/A
        a1 =  -2*cos_w0
        a2 =   1 - alpha/A

        return np.array([b0, b1, b2, a0, a1, a2]) / a0

    def start_stream(self, device_index=None):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        print(f"DEBUG: Opening audio stream (Device: {device_index})")
        try:
            self.stream = self.p.open(format=self.FORMAT,
                                      channels=self.CHANNELS,
                                      rate=self.RATE,
                                      input=True,
                                      input_device_index=device_index,
                                      frames_per_buffer=self.CHUNK) # No large buffer
            print("DEBUG: Audio stream opened.")
        except Exception as e:
            print(f"ERROR: Failed to open stream: {e}")

    def get_input_devices(self):
        devices = []
        try:
            info = self.p.get_host_api_info_by_index(0)
            numdevices = info.get('deviceCount')
            for i in range(0, numdevices):
                if (self.p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                    name = self.p.get_device_info_by_host_api_device_index(0, i).get('name')
                    devices.append((i, name))
        except Exception as e:
            pass
        return devices

    def set_gain(self, gain):
        self.gain = max(0.0, float(gain))

    def set_pitch(self, factor):
        self.pitch_factor = max(0.1, min(4.0, float(factor)))

    def set_eq(self, low, mid, high):
        self.eq_low_db = low
        self.eq_mid_db = mid
        self.eq_high_db = high

    def _shift_pitch_fft(self, audio_chunk, factor):
        """
        Naive pitch shift using FFT scaling.
        Produces robotic/alien artifacts but maintains strict 1:1 timing (zero latency drift).
        """
        # Stereo Handling: Process as mono temporarily or interleaved?
        # FFT is easier on mono or separate channels. Interleaved is messy.
        # Let's reshape to (N_samples, Channels)
        shape = audio_chunk.shape
        audio_chunk = audio_chunk.reshape(-1, self.CHANNELS)
        
        # Windowing to reduce click artifacts at boundaries
        n_samples = audio_chunk.shape[0]
        # window = np.hanning(n_samples)[:, np.newaxis] # simple window
        
        # FFT (Real)
        # axis=0 is time
        freq_domain = np.fft.rfft(audio_chunk, axis=0)
        
        # Scaling indices
        n_freqs = freq_domain.shape[0]
        indices = np.arange(n_freqs)
        # If pitch > 1.0 (higher), we want lower freqs to move to higher indices.
        # target_index = src_index / factor
        # e.g. factor 2.0: index 10 comes from index 5? No.
        # Shift UP: F_new = F_old * factor.
        # Index_new = Index_old * factor.
        # content at Index_new comes from Index_new / factor.
        
        # Interpolation source indices
        new_indices = indices / factor
        
        # Clip indices to valid range
        new_indices = np.clip(new_indices, 0, n_freqs - 1)
        
        # Interpolate Magnitude and Phase separately?
        # For robot voice, magnitude is key. Phase randomization adds robot feel.
        # Naive complex interpolation:
        # We need to interpolate Real and Imag separately
        
        shifted_real = np.zeros_like(freq_domain.real)
        shifted_imag = np.zeros_like(freq_domain.imag)
        
        for ch in range(self.CHANNELS):
             shifted_real[:, ch] = np.interp(new_indices, indices, freq_domain[:, ch].real)
             shifted_imag[:, ch] = np.interp(new_indices, indices, freq_domain[:, ch].imag)
        
        shifted_freq_domain = shifted_real + 1j * shifted_imag
        
        # IFFT
        shifted_time = np.fft.irfft(shifted_freq_domain, n=n_samples, axis=0)
        
        return shifted_time.flatten().astype(np.float32)

    def read(self):
        try:
            if self.stream is None or not self.stream.is_active():
                 return b'\x00' * self.CHUNK * 4

            # Always read exactly CHUNK size (maintain real-time sync)
            try:
                data = self.stream.read(self.CHUNK, exception_on_overflow=False)
            except IOError:
                # Buffer overflow/underflow, return silence to catch up
                return b'\x00' * self.CHUNK * 4
            
            audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32)

            # 1. Pitch Shift (FFT-based, Zero Latency)
            if self.pitch_factor != 1.0:
                 audio_data = self._shift_pitch_fft(audio_data, self.pitch_factor)

            # 2. Apply EQ
            if abs(self.eq_low_db) > 0.1:
                coeffs = self._design_low_shelf(100, self.eq_low_db)
                audio_data = scipy.signal.lfilter(coeffs[:3], coeffs[3:], audio_data)

            if abs(self.eq_mid_db) > 0.1:
                coeffs = self._design_peaking(1000, self.eq_mid_db)
                audio_data = scipy.signal.lfilter(coeffs[:3], coeffs[3:], audio_data)

            if abs(self.eq_high_db) > 0.1:
                coeffs = self._design_high_shelf(8000, self.eq_high_db)
                audio_data = scipy.signal.lfilter(coeffs[:3], coeffs[3:], audio_data)

            # 3. Apply Gain
            if self.gain != 1.0:
                audio_data = audio_data * self.gain

            # 4. Clip
            audio_data = np.clip(audio_data, -32768, 32767)
            return audio_data.astype(np.int16).tobytes()

        except Exception as e:
            # print(f"Audio Error: {e}")
            return b'\x00' * self.CHUNK * 4

    def cleanup(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()

    def is_opus(self):
        return False
