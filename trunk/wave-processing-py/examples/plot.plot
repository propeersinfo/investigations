set terminal png
#set title 'file.wav'
set output '1.png'

set multiplot layout 2, 1 title "file.wav"

#set title "Fill area between two curves"
#set xrange [0:*]
#set yrange [-32768:32768]
set style data lines
plot '1.dat' u 1:2:3 w filledcu notitle

set style data lines
plot '1.dat' u 1:4:5 w filledcu notitle

unset multiplot


# plot with outline
# plot '1.dat' u 1:4:5 w filledcu, '' u 1:4 lt -1 notitle, '' u 1:5 lt -1 notitle