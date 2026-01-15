import numpy as np
#import pyaudio
from scipy import signal
import scipy
import streamlit as st

st.title("Custom synth generator")
st.caption("Created by Drew Warner")

def gen_harmonic_series(base_freq, num_harmonics):#num harmonics must be at least 1
    output = []
    for i in range(1, num_harmonics+1):
        output.append(base_freq*i)
    return output

def gen_volume_series(mult_factor, count):#generate exponential decay series starting at 1, multiplying each time by mult_factor
    output = []
    for i in range(count):
        output.append(mult_factor**i)
    return output

def sin_gen(frequencies, strengths, duration, fs):#generate all the sine waves in one output
    #strengths is what the frequencies' volumes are * by, in order
    samples = np.float32()
    for i in range(len(frequencies)):
        f = frequencies[i]
        samples += ((np.sin(2*np.pi*np.arange(fs*duration)*f/fs)).astype(np.float32))*strengths[i]
    return samples

def saw_gen(frequencies, strengths, duration, fs):#same as sin_gen, but sawtooth
    samples = np.float32()
    for i in range(len(frequencies)):
        f = frequencies[i]
        t = np.linspace(0, duration, int(fs*duration), endpoint=False)#gen time for sawtooth
        samples+=((signal.sawtooth(2*np.pi*f*t)).astype(np.float32)*strengths[i])
    return samples


def square_gen(frequencies, strengths, duration, fs):#same as sin_gen, but square
    samples = np.float32()
    for i in range(len(frequencies)):
        f = frequencies[i]
        t = np.linspace(0, duration, int(fs*duration), endpoint=False)#gen time for sawtooth
        samples+=((signal.square(2*np.pi*f*t)).astype(np.float32)*strengths[i])
    return samples


#samples = square_gen(gen_harmonic_series(440, 80), gen_volume_series(0.7, 80), duration, fs)


frequency = st.number_input("Select demo frequency", 1.0, 20000.0, 440.0)
sample_rate = st.number_input("Select sample rate", 1, 100000000, 44100)

st.subheader("Sine")
sin_volume_proportion = st.slider("Select a relative volume for the sine component: ", 0, 100, 80)
sin_harmonic_count = st.number_input("Select number of harmonics (at least 1, for base frequency)", 1, 1000, 80, key='sin1')
sin_harmonic_volume_decay = st.number_input("Select the harmonic volume decay (i.e. 0.5 = each one is half as loud as the last)", 0.0, 1.0, 0.3, key='sin2')

st.space(size="small")

st.subheader("Saw")
saw_volume_proportion = st.slider("Select a relative volume for the saw wave component: ", 0, 100, 0)
saw_harmonic_count = st.number_input("Select number of harmonics (at least 1, for base frequency)", 1, 1000, 1, key='saw1')
saw_harmonic_volume_decay = st.number_input("Select the harmonic volume decay (i.e. 0.5 = each one is half as loud as the last)", 0.0, 1.0, 0.8, key='saw2')

st.space(size="small")

st.subheader("Square")

square_volume_proportion = st.slider("Select a relative volume for the square component: ", 0, 100, 10)
square_harmonic_count = st.number_input("Select number of harmonics (at least 1, for base frequency)", 1, 1000, 5, key='sqr1')
square_harmonic_volume_decay = st.number_input("Select the harmonic volume decay (i.e. 0.5 = each one is half as loud as the last)", 0.0, 1.0, 0.8, key='sqr2')

st.space(size="small")

if st.button("Generate audio sample"):
    total_volumes = (sin_volume_proportion+saw_volume_proportion+square_harmonic_volume_decay)
    #balance by dividing
    sin_volume_proportion /= total_volumes
    saw_volume_proportion /= total_volumes
    square_volume_proportion /= total_volumes

    #with st.spinner("Loading audio stream"):#pyaudio version
    #    p = pyaudio.PyAudio()
    volume = 0.5#0-1
    fs = sample_rate#sample rate
    duration = 1.0#seconds
    f = float(frequency)#Hz

    with st.spinner("Generating waves"):
        samples = np.float32()
        samples += sin_gen(gen_harmonic_series(f, sin_harmonic_count), gen_volume_series(sin_harmonic_volume_decay, sin_harmonic_count), duration, fs)*sin_volume_proportion
        samples += saw_gen(gen_harmonic_series(f, saw_harmonic_count), gen_volume_series(saw_harmonic_volume_decay, saw_harmonic_count), duration, fs)*saw_volume_proportion
        samples += square_gen(gen_harmonic_series(f, square_harmonic_count), gen_volume_series(square_harmonic_volume_decay, square_harmonic_count), duration, fs)*square_volume_proportion
    
    with st.spinner("Outputting sample"):
        scipy.io.wavfile.write("sample.wav", sample_rate, volume*samples)
        st.audio("sample.wav", format="audio/wav")
        #below uses the pyaudio
        #output_bytes = (volume*samples).tobytes()
        #stream = p.open(format=pyaudio.paFloat32, channels=1, rate=fs, output=True)
        #stream.write(output_bytes)
        #stream.stop_stream()
    #with st.spinner("Cleaning up"):
    #    stream.close()
    #    p.terminate()