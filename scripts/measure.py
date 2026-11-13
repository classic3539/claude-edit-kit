#!/usr/bin/env python3
"""Measure a video: the same ruler for reference edits and for your renders.

    .venv/bin/python scripts/measure.py renders/edit.mp4 [--no-transcript]

Prints JSON: duration, shot count, average shot length, cuts per minute, frozen stretches,
black frames, dead air, loudness. Saves frames to look at in <name>-frames/ (about 1 per
second, at most 120) and, unless --no-transcript, a transcript of the video itself.
Shot detection uses a scene-change threshold, so treat shot numbers as close, not exact.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

SCENE = 0.3          # scene-change threshold for counting cuts
FREEZE_S = 0.5       # a picture that doesn't move for this long is flagged
BLACK_S = 0.1
SILENCE_DB, SILENCE_S = -40, 0.7
MAX_FRAMES = 120


def ff(args):
    return subprocess.run(['ffmpeg', '-hide_banner', '-nostats', *args], capture_output=True, text=True).stderr


def duration(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(path)],
                         capture_output=True, text=True).stdout.strip()
    return float(out)


def has_audio(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=index', '-of', 'csv=p=0', str(path)],
                         capture_output=True, text=True).stdout.strip()
    return bool(out)


def measure(path, transcript=True):
    path = Path(path).resolve()
    dur = duration(path)
    audio = has_audio(path)

    # one pass over the picture: cuts, freezes, black frames
    vf = f"select='gt(scene,{SCENE})',showinfo"
    cuts = [round(float(t), 2) for t in re.findall(r'pts_time:([\d.]+)', ff(['-i', str(path), '-vf', vf, '-an', '-f', 'null', '-']))]
    err = ff(['-i', str(path), '-vf', f'freezedetect=n=0.003:d={FREEZE_S},blackdetect=d={BLACK_S}:pix_th=0.10', '-an', '-f', 'null', '-'])
    starts = [float(x) for x in re.findall(r'freeze_start: ([\d.]+)', err)]
    lens = [float(x) for x in re.findall(r'freeze_duration: ([\d.]+)', err)]
    freezes = [{'at': round(s, 2), 'seconds': round(d, 2)} for s, d in zip(starts, lens)]
    if len(starts) > len(lens):                       # frozen until the end
        freezes.append({'at': round(starts[-1], 2), 'seconds': round(dur - starts[-1], 2)})
    blacks = [{'at': round(float(a), 2), 'seconds': round(float(c), 2)}
              for a, _, c in re.findall(r'black_start:([\d.]+) black_end:([\d.]+) black_duration:([\d.]+)', err)]

    # sound: dead air and loudness
    silences, loud = [], {}
    if audio:
        err = ff(['-i', str(path), '-vn', '-af', f'silencedetect=n={SILENCE_DB}dB:d={SILENCE_S},ebur128=peak=true', '-f', 'null', '-'])
        s_at = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', err)]
        s_len = [float(x) for x in re.findall(r'silence_duration: ([\d.]+)', err)]
        silences = [{'at': round(a, 2), 'seconds': round(d, 2)} for a, d in zip(s_at, s_len)]
        summary = err.split('Summary:')[-1]
        for key, pat in (('integrated_lufs', r'I:\s+(-?[\d.]+) LUFS'), ('range_lu', r'LRA:\s+(-?[\d.]+) LU'),
                         ('true_peak_dbfs', r'Peak:\s+(-?[\d.]+) dBFS')):
            m = re.search(pat, summary)
            if m: loud[key] = float(m.group(1))

    shots = len(cuts) + 1
    # frames to look at
    frames_dir = path.parent / f'{path.stem}-frames'
    shutil.rmtree(frames_dir, ignore_errors=True)
    frames_dir.mkdir()
    every = max(1.0, dur / MAX_FRAMES)
    ff(['-i', str(path), '-vf', f'fps=1/{every:.3f},scale=540:-2', '-q:v', '4', str(frames_dir / 'f%04d.jpg')])

    report = {
        'file': path.name,
        'duration_s': round(dur, 2),
        'shots': shots,
        'avg_shot_s': round(dur / shots, 2),
        'cuts_per_min': round(len(cuts) / dur * 60, 1) if dur else 0,
        'cut_times': cuts,
        'frozen': freezes,
        'black': blacks,
        'dead_air': silences,
        'longest_dead_air_s': max((s['seconds'] for s in silences), default=0),
        'loudness': loud if audio else 'no audio track',
        'frames': {'dir': str(frames_dir), 'every_s': round(every, 2), 'count': len(list(frames_dir.glob('*.jpg')))},
    }
    if transcript and audio:
        sys.path.insert(0, str(Path(__file__).parent))
        from transcribe import words_of
        words, sentences = words_of(path)
        txt = path.with_suffix('.transcript.txt')
        txt.write_text(''.join(f"[{s['start']:.2f}-{s['end']:.2f}] {s['text']}\n" for s in sentences))
        report['transcript'] = {'file': str(txt), 'words': len(words),
                                'words_per_min': round(len(words) / dur * 60) if dur else 0}
    return report


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) != 1:
        sys.exit(__doc__)
    print(json.dumps(measure(args[0], transcript='--no-transcript' not in sys.argv), indent=1))
