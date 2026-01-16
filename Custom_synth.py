import numpy as np
#import pyaudio
from scipy import signal
import scipy
import streamlit as st
import pretty_midi
import math
import plotly.graph_objects as go

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
        t = np.linspace(0, duration, int(math.ceil(fs*duration)), endpoint=False)#gen time for sawtooth
        samples+=((signal.sawtooth(2*np.pi*f*t)).astype(np.float32)*strengths[i])
    return samples


def square_gen(frequencies, strengths, duration, fs):#same as sin_gen, but square
    samples = np.float32()
    for i in range(len(frequencies)):
        f = frequencies[i]
        t = np.linspace(0, duration, int(math.ceil(fs*duration)), endpoint=False)#gen time
        samples += ((signal.square(2*np.pi*f*t)).astype(np.float32)*strengths[i])
    return samples


#samples = square_gen(gen_harmonic_series(440, 80), gen_volume_series(0.7, 80), duration, fs)



sample_rate = st.number_input("Select sample rate", 1, 100000000, 44100)
smoothing_rounds = st.number_input("Select a number of smoothing rounds for the output wave (rolling average)", 0, 100, 0)

st.subheader("Sine")
sin_volume_proportion = st.slider("Select a relative volume for the sine component: ", 0, 100, 80)
sin_harmonic_count = st.number_input("Select number of harmonics (at least 1, for base frequency)", 1, 1000, 10, key='sin1')
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

frequency = st.number_input("Select demo frequency", 1.0, 20000.0, 440.0)

st.space(size='small')

if st.button("Generate audio sample"):
    total_volumes = (sin_volume_proportion+saw_volume_proportion+square_volume_proportion)
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

        #add the rolling average to the wave
        if smoothing_rounds != 0:
            for _ in range(smoothing_rounds):
                samples = np.convolve(samples, np.ones(3, dtype=np.float32)/3, mode="same")
            

        
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

    #draw a graph of the wave
    st.caption("Waveform")
    with st.spinner("Plotting waveform"):
        x = np.arange(len(samples[:int(1/f*4*fs)]))
        st.plotly_chart(go.Figure(go.Scatter(x=x, y=samples[:int(1/f*4*fs)], mode="lines")))
    

st.header("MIDI synthesization")
st.caption("Upload a midi file to synthesize")
midi_file = st.file_uploader("Upload MIDI here", type=['midi', 'mid', 'smf', 'kar'])
volume_reduction = st.number_input("Input the volume reduction of each note here (reduced times this amount, prevents overdrive). Recommended 5", 1, 100000, 5)
attack_length_in = st.number_input("Input the length of the attack (0-100% volume at the start of the note) in seconds. Keep this low. ", 0.0, 999999999.0, 0.01)
fade_length_in = st.number_input("Input the length of the fade out of the note in seconds. Set high (maybe 500) to make piano-like sounds.", 0.0, 999999999.0, 0.01)#upper bound here is high to allow for piano-like fade
if st.button("Start processing"):
    if midi_file:
        with st.spinner("Loading file..."):
            midi_data = pretty_midi.PrettyMIDI(midi_file)
        current_time = 0.0
        midi_data_end = midi_data.get_end_time()
        output_buffer = np.zeros(int(np.ceil(midi_data_end*sample_rate)), dtype=np.float32)
        #balance volumes, by dividing
        total_volumes = (sin_volume_proportion+saw_volume_proportion+square_volume_proportion)
        sin_volume_proportion /= total_volumes
        saw_volume_proportion /= total_volumes
        square_volume_proportion /= total_volumes

        #load each note from the midi and add it to the correct slices of the output buffer
        
        completion = st.progress(0,"Progress")
        i = 0
        for instrument in midi_data.instruments:
            j=0
            for note in instrument.notes:
                
                frequency = pretty_midi.note_number_to_hz(note.pitch)
                volume = note.velocity/127#velocity is basically how hard key is hit, basically volume. Corrected to 0-1 range
                start = note.start*sample_rate#adjusted for samples to insert into output buffer
                end = note.end*sample_rate
                #now that we have all the information, make the note.


                fs = sample_rate#sample rate
                duration = (end-start)/sample_rate
                f = float(frequency)#Hz
                samples = np.float32()
                samples += sin_gen(gen_harmonic_series(f, sin_harmonic_count), gen_volume_series(sin_harmonic_volume_decay, sin_harmonic_count), duration, fs)*sin_volume_proportion
                samples += saw_gen(gen_harmonic_series(f, saw_harmonic_count), gen_volume_series(saw_harmonic_volume_decay, saw_harmonic_count), duration, fs)*saw_volume_proportion
                samples += square_gen(gen_harmonic_series(f, square_harmonic_count), gen_volume_series(square_harmonic_volume_decay, square_harmonic_count), duration, fs)*square_volume_proportion
                
                #add the rolling average to the wave
                if smoothing_rounds != 0:
                    for _ in range(smoothing_rounds):
                        samples = np.convolve(samples, np.ones(3, dtype=np.float32)/3, mode="same")
            
                
                samples*=volume
                samples/=float(volume_reduction)

                #Make the gradual attack.
                attack_length = int(attack_length_in*sample_rate)#by indicies/frames of output
                if attack_length >= len(samples):
                    attack_length = len(samples)-1
                slope = 1/attack_length#y=mx+b, b being 0, m being this
                attack = []
                for x in range(attack_length):
                    attack.append(float(x)*slope)
                
                #apply the attack
                samples[:attack_length] *= np.array(attack, dtype=np.float32)

                #Make the gradual cutoff at the end
                fade_length = int(fade_length_in*sample_rate)
                if fade_length >= len(samples):
                    fade_length = len(samples)-1
                slope = -1/fade_length#y=mx+1, this being m
                fade = []
                for x in range(fade_length):
                    fade.append((float(x)*slope)+1)
                
                #apply the fade
                samples[-fade_length:] *= np.array(fade, dtype=np.float32)

                output_buffer[int(start):int(start)+len(samples)]+=samples

                #update progress
                j += 1
                prog = (j/len(instrument.notes))/len(midi_data.instruments)+(i/len(midi_data.instruments))
                if prog > 1.0:#prevent streamlit error if something goes wrong here
                    prog = 1.0
                completion.progress(prog)
            i+=1
            



        #output the midi itself
        with st.spinner("Outputting sound file"):
            scipy.io.wavfile.write("rendered.wav", sample_rate, output_buffer)
            st.audio("rendered.wav", format="audio/wav")
    else:#if no midi file was provided but button was pressed
        st.error("No midi file provided")

            

