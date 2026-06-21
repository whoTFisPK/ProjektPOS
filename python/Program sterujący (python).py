"""
Skrypt realizuje w pełni zautomatyzowane pozycjonowanie geometryczne oraz akwizycję
i cyfrowe przetwarzanie sygnałów akustycznych w celu wyznaczenia odpowiedzi impulsowych HRTF.
Współpracuje z układem Arduino przez port UART i przetwarza sygnały metodą dekonwolucji sweep-sine.

Wykorzystywane biblioteki zewnętrzne: numpy, serial, matplotlib, sounddevice, soundfile, scipy.signal.
"""
import numpy as np
import serial
import time
import matplotlib.pyplot as plt
import sounddevice as sd
import soundfile as sf
import scipy.signal as sig 

#PARAMETRY SFERY
N = 20
steps_per_turn = 3200 # liczba kroków na pełny obrót

# Obliczenia wstępne
r = 1
a = 4 * np.pi * r * r / N
d = np.sqrt(a)
Mtheta = round(np.pi / d)
dtheta = np.pi / Mtheta
dphi = a / dtheta

# Listy punktów
X = []
Y = []
Z = []
ThetaList = []
PhiList = []

# GENEROWANIE PUNKTÓW NA SFERZE
for m in range(Mtheta):
    theta = np.pi * (m + 0.5) / Mtheta
    Mphi = round(2 * np.pi * np.sin(theta) / dphi)

    for n in range(Mphi):
        phi = 2 * np.pi * n / Mphi
        
        x = r * np.sin(theta) * np.cos(phi)
        y = r * np.sin(theta) * np.sin(phi)
        z = r * np.cos(theta)
        
        X.append(x)
        Y.append(y)
        Z.append(z)
        ThetaList.append(theta)
        PhiList.append(phi)

print("Liczba punktów:", len(X))

# WIZUALIZACJA
fig = plt.figure(figsize=(12, 6))

# 3D
ax1 = fig.add_subplot(1, 2, 1, projection="3d")
u, v = np.mgrid[0:2*np.pi:50j, 0:np.pi:50j]
ax1.plot_surface(r*np.cos(u)*np.sin(v),
                 r*np.sin(u)*np.sin(v),
                 r*np.cos(v),
                 alpha=0.2, color="lightblue")
ax1.scatter(X, Y, Z, c='red')
ax1.set_title("Punkty na sferze 3D")
ax1.set_xlabel("X"); ax1.set_ylabel("Y"); ax1.set_zlabel("Z")

# Theta–Phi
ax2 = fig.add_subplot(1, 2, 2)
ax2.scatter(PhiList, ThetaList)
ax2.set_xlabel(r'$\phi$ [rad]')
ax2.set_ylabel(r'$\theta$ [rad]')
ax2.set_title("Wykres azymutalno-zenitalny")
ax2.set_xlim([0, 2*np.pi])
ax2.set_ylim([0, np.pi])

plt.tight_layout()
plt.show()

# POMIAR
def measure_ir_sweep(
    sweep_file="Sweep-20-20000-1s.wav",
    sweep_rev_file="Sweep-20-20000-1s-rev.wav",
    channels_in=2,
    input_device=1,
    output_device=3,
    samplerate=48000,
    point_id=None,
    pre_ms=0.3,
    post_ms=15):
    
    """
    Główna procedura pomiarowa. Odpowiada za jednoczesne odtwarzanie sygnału testowego
    oraz rejestrację odpowiedzi układu, a także za późniejsze operacje matematyczne 
    (dekonwolucja, ekstrakcja, okienkowanie czasowe).

    Argumenty:
    sweep_file (str): Ścieżka do pliku wejściowego z sygnałem pobudzenia log-sweep.
    sweep_rev_file (str): Ścieżka do pliku z filtrem odwrotnym do operacji splotu.
    channels_in (int): Liczba kanałów wejściowych rejestracji (standardowo 2).
    input_device (int): Indeks sprzętowy karty dźwiękowej (wejście).
    output_device (int): Indeks sprzętowy karty dźwiękowej (wyjście).
    samplerate (int): Częstotliwość próbkowania audio w Hz.
    point_id (int): Aktualny numer identyfikacyjny punktu pomiarowego.
    pre_ms (float): Margines czasu przed początkiem odpowiedzi impulsowej (w ms).
    post_ms (float): Długość okna czasowego analizy odpowiedzi właściwej (w ms).

    Zwraca:
    tuple(np.ndarray, np.ndarray): Znormalizowane odpowiedzi impulsowe HRIR lewego i prawego kanału.
    """
    sweep, sr = sf.read(sweep_file, dtype="float32")
    sweep_rev, sr2 = sf.read(sweep_rev_file, dtype="float32")
    
    assert sr == samplerate
    assert sr2 == samplerate
    
    data_out = sweep
    
    sd.default.device = (input_device, output_device)
    sd.default.samplerate = samplerate

    time.sleep(1)
    print("Odtwarzanie sygnału i nagrywanie...")
    recorded = sd.playrec(data_out, samplerate=samplerate,
    channels=channels_in, dtype="float32")
    sd.wait()
    print("Nagranie zakończone.")

    time.sleep(1)
    
    raw_left = recorded[:, 0]
    raw_right = recorded[:, 1]
    
    sf.write(f"RAW_left_point_{point_id:02}.wav", raw_left, samplerate)
    sf.write(f"RAW_right_point_{point_id:02}.wav", raw_right, samplerate)

    # Dekonwolucja
    ir_left = sig.convolve(raw_left, sweep_rev, mode="full")
    ir_right = sig.convolve(raw_right, sweep_rev, mode="full")

    # Detekcja początku odpowiedzi
    threshold = 0.1 * np.max(np.abs(ir_left))
    t0_left = np.where(np.abs(ir_left) > threshold)[0][0]
    threshold = 0.1 * np.max(np.abs(ir_right))
    t0_right = np.where(np.abs(ir_right) > threshold)[0][0]

    # wspólny t0 (opcjonalnie)
    t0 = min(t0_left, t0_right)

    # Bramkowanie czasowe
    pre = int(pre_ms * 1e-3 * samplerate)
    post = int(post_ms * 1e-3 * samplerate)
    hrir_left = ir_left[t0 - pre: t0 + post]
    hrir_right = ir_right[t0 - pre: t0 + post]
    
    # Okno wygładzające (Tukey)
    window = sig.windows.tukey(len(hrir_left), alpha=0.25)
    hrir_left *= window
    hrir_right *= window

    # Finalna normalizacja
    hrir_left /= np.max(np.abs(hrir_left))
    hrir_right /= np.max(np.abs(hrir_right))
    return hrir_left.astype(np.float32), hrir_right.astype(np.float32)

# POŁĄCZENIE Z ARDUINO
arduino_port = "COM4" # ZMIENIĆ NA SWÓJ PORT!
baudrate = 115200

print("Otwieranie portu...")
ser = serial.Serial(arduino_port, baudrate, timeout=1)

# Arduino resetuje się przy otwarciu portu
time.sleep(2)
print("Arduino gotowe")

# WYSYŁANIE DANYCH DO ARDUINO

# współrzędne startowe
prev_theta = 0
prev_phi = 0

ThetaList.append(prev_theta)
PhiList.append(prev_phi)

last_point = len(ThetaList) - 1

for i, (theta, phi) in enumerate(zip(ThetaList, PhiList)):
    print("\nPunkt", i+1)
    delta_theta = theta - prev_theta
    delta_phi = phi - prev_phi

    steps_theta = round(delta_theta * steps_per_turn / (2*np.pi))
    steps_phi = round(delta_phi * steps_per_turn / (2*np.pi))
    dir_theta = 0 if steps_theta >= 0 else 1
    dir_phi = 0 if steps_phi >= 0 else 1

    print("Δtheta =", delta_theta, "→", steps_theta, "kroków")
    print("Δphi =", delta_phi, "→", steps_phi, "kroków")
    print("dir_theta =", dir_theta)
    print("dir_phi =", dir_phi)

    message = f"{abs(steps_theta)},{abs(steps_phi)},{dir_theta},{dir_phi}\n"
    ser.write(message.encode())

    # ODBIERANIE ODPOWIEDZI
    while True:
        response = ser.readline().decode().strip()
        if response:
            print("Arduino:", response)
            if response == "done":
                break
    
    prev_theta = theta
    prev_phi = phi

if i == last_point:
    print("Ostatni punkt, pomijam pomiar IR...")
else:
    # Pomiar IR
    hrir_left, hrir_right = measure_ir_sweep(
        sweep_file="Sweep-20-20000-1s.wav",
        sweep_rev_file="Sweep-20-20000-1s-rev.wav",
        point_id=i + 1
    )
    # Zapis odpowiedzi impulsowych do pliku WAV
    filename_left = f"HRIR_left_point_{i + 1:02}.wav"
    filename_right = f"HRIR_right_point_{i + 1:02}.wav"
    sf.write(filename_left, hrir_left, 48000)
    sf.write(filename_right, hrir_right, 48000)
    print(f"Zapisano {filename_left} oraz {filename_right}")

ser.close()
print("\nZakończono komunikację.")