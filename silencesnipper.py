import subprocess, os, sys, re

# Sort out the keyword arguments
path = sys.argv[1]
threshold = sys.argv[2]
min_duration = sys.argv[3]

print('Path is ' + str(path))
print('Threshold is ' + str(threshold))
print('Minimum duration is ' + str(min_duration))

# Make a List of all video files in the folder
raw_clips = []
for name in os.listdir(path):
    if name.endswith('.mp4'):
        raw_clips.append(name)

# Clean the ffmpeg output to get just the silences
def getSilences(clip):
    print('Getting silences for ' + clip)
    ffmpeg_output = subprocess.run(
        'ffmpeg -hide_banner -vn -i {} -af silencedetect=n={}dB:d={} -f null - 2>&1 | findstr "silence_end"'
        .format(clip, threshold, min_duration),
        shell=True, capture_output=True, text=True
    )
    ffmpeg_numbers = re.findall('\d+\.\d+', ffmpeg_output.stdout)
    silences = []
    for i in range(len(ffmpeg_numbers)):
        ffmpeg_numbers[i] = float(ffmpeg_numbers[i])
    for i in range(len(ffmpeg_numbers)):
        if i % 2 == 0:
            silences.append((ffmpeg_numbers[i], ffmpeg_numbers[i+1]))
    refined_silences = []
    for i in silences:
        refined_silences.append((i[0] - i[1], i[0]))
    print(str(len(refined_silences)) + ' silences found:')
    for i in refined_silences:
        print(i)
    return refined_silences

# Trim the file and output to alternative file
def getTrim(clip, start, end, output):
    print('Trimming ' + clip + '...')
    subprocess.run('ffmpeg -hide_banner -i {} -ss {} -to {} {}'
                    .format(clip, start, end, output),
                    shell=True)
    print('Trim finished.')

# This should contain the logic of when/what to trim
def main():
    for i in raw_clips:
        silences = getSilences(i)
        if len(silences) > 1:
            # Grab the raw clip's duration and clean it
            print('Grabbing duration for {}...'.format(i))
            clip_duration = subprocess.run(
                'ffprobe -hide_banner -v error -select_streams v:0 -show_entries stream=duration -of default=nw=1:nk=1 {}'
                .format(i),
                shell=True, capture_output=True, text=True
            )
            clip_duration = float(re.findall('\d*\.\d*', clip_duration.stdout)[0])
            print('Duration is ' + str(clip_duration))

            # Looking for suitable edit points at start and end of raw clip
            viable_starts = []
            viable_ends = []
            for silence in silences:
                if silence[0] < clip_duration * 0.4:
                    viable_starts.append(silence)
                elif silence[1] > clip_duration * 0.6:
                    viable_ends.append(silence)
            print('{} has '.format(i) + str(len(viable_starts)) + ' viable intro points.')
            print('{} has '.format(i) + str(len(viable_ends)) + ' viable outro points.')

            # Call trimming function if we've got viable edit points
            output = str(i)[:2] + 'a' + str(i)[2:]
            if len(viable_starts) > 0 and len(viable_ends) > 0:
                getTrim(i, str(viable_starts[0][0]), str(viable_ends[-1][1]), output)

if __name__ == '__main__':
    main()
