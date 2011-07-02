SET WAV=pluton
SET WAV=1

..\cat-wave.py ..\wav\%WAV%.wav | ..\plot-waveform.py > 1.dat
cat plot.plot | C:\Portable\gnuplot\bin\gnuplot.exe
1.png