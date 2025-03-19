import time

TONES = {
  "B0": 31,
  "C1": 33,
  "CS1": 35,
  "D1": 37,
  "DS1": 39,
  "E1": 41,
  "F1": 44,
  "FS1": 46,
  "G1": 49,
  "GS1": 52,
  "A1": 55,
  "AS1": 58,
  "B1": 62,
  "C2": 65,
  "CS2": 69,
  "D2": 73,
  "DS2": 78,
  "E2": 82,
  "F2": 87,
  "FS2": 93,
  "G2": 98,
  "GS2": 104,
  "A2": 110,
  "AS2": 117,
  "B2": 123,
  "C3": 131,
  "CS3": 139,
  "D3": 147,
  "DS3": 156,
  "E3": 165,
  "F3": 175,
  "FS3": 185,
  "G3": 196,
  "GS3": 208,
  "A3": 220,
  "AS3": 233,
  "B3": 247,
  "C4": 262,
  "CS4": 277,
  "D4": 294,
  "DS4": 311,
  "E4": 330,
  "F4": 349,
  "FS4": 370,
  "G4": 392,
  "GS4": 415,
  "A4": 440,
  "AS4": 466,
  "B4": 494,
  "C5": 523,
  "CS5": 554,
  "D5": 587,
  "DS5": 622,
  "E5": 659,
  "F5": 698,
  "FS5": 740,
  "G5": 784,
  "GS5": 831,
  "A5": 880,
  "AS5": 932,
  "B5": 988,
  "C6": 1047,
  "CS6": 1109,
  "D6": 1175,
  "DS6": 1245,
  "E6": 1319,
  "F6": 1397,
  "FS6": 1480,
  "G6": 1568,
  "GS6": 1661,
  "A6": 1760,
  "AS6": 1865,
  "B6": 1976,
  "C7": 2093,
  "CS7": 2217,
  "D7": 2349,
  "DS7": 2489,
  "E7": 2637,
  "F7": 2794,
  "FS7": 2960,
  "G7": 3136,
  "GS7": 3322,
  "A7": 3520,
  "AS7": 3729,
  "B7": 3951,
  "C8": 4186,
  "CS8": 4435,
  "D8": 4699,
  "DS8": 4978
}

INSTRUCTION_TONES = {
  "Beep it!": ["G6", "C4"],
  "Flick it!": [("G4", "D5", 0.2)],
  "Shake it!": ["E5", "C5", "G4"],
  "Slide it!": [("D4", "A4", 0.3)],
  "GAME_START": ["C5", "G4", "E4", "A4", "B4", "G4"],
  "SUCCESS": [("DS5", "D6", 0.3)],
  "FAILURE": [("D6", 'DS3', 0.3)]
}

def playtone(buzzer, frequency, duration=0.2):
    if frequency > 0:
        buzzer.freq(frequency)
        buzzer.duty_u16(16384)  # 25% duty cycle
        time.sleep(duration)
    bequiet(buzzer)

def playsweep(buzzer, start_tone, end_tone, duration=0.3, steps=20):
    """Sweeps the buzzer from start_tone to end_tone smoothly."""
    start_freq = TONES.get(start_tone, 0)
    end_freq = TONES.get(end_tone, 0)
    step_delay = duration / steps
    freq_step = (end_freq - start_freq) / steps

    for i in range(steps):
        freq = int(start_freq + (i * freq_step))
        playtone(buzzer, freq, step_delay)

def bequiet(buzzer):
    buzzer.duty_u16(0)

def playsong(buzzer, song_name):
    song = INSTRUCTION_TONES[song_name]
    for note in song:
        if isinstance(note, tuple):
            playsweep(buzzer, *note)
        else:
            frequency = TONES.get(note, 0)
            playtone(buzzer, frequency)
