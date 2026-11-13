#!/usr/bin/env python3
"""Word-level transcript of a video or audio file, with parakeet-mlx (runs locally on Apple Silicon).

    .venv/bin/python scripts/transcribe.py footage/clip.mov

Writes next to the input:
    clip.words.json  [{"word", "start", "end"}, ...] in seconds, for cutting on exact words
    clip.txt         one line per sentence: [start-end] text, for reading and planning cuts
Audio is transcribed in 2-minute chunks: an unchunked long file can run a 16 GB Mac out of memory.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

MODEL = 'mlx-community/parakeet-tdt-0.6b-v3'
CHUNK_S, OVERLAP_S = 120, 15


def words_of(path):
    """Return (words, sentences) for any file ffmpeg can read."""
    from parakeet_mlx import from_pretrained
    with tempfile.TemporaryDirectory() as d:
        wav = Path(d) / 'audio.wav'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(path), '-vn', '-ac', '1', '-ar', '16000', str(wav)], check=True)
        r = from_pretrained(MODEL).transcribe(wav, chunk_duration=CHUNK_S, overlap_duration=OVERLAP_S)
    words, sentences = [], []
    for s in r.sentences:
        cur = None
        for t in s.tokens:
            if cur is None or t.text.startswith(' '):
                cur = {'word': t.text.strip(), 'start': round(t.start, 3), 'end': round(t.end, 3)}
                words.append(cur)
            else:
                cur['word'] += t.text
                cur['end'] = round(t.end, 3)
        sentences.append({'start': round(s.start, 3), 'end': round(s.end, 3), 'text': s.text.strip()})
    return [w for w in words if w['word']], sentences


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1]).resolve()
    if not src.exists():
        sys.exit(f'not found: {src}')
    words, sentences = words_of(src)
    stem = src.with_suffix('')
    Path(f'{stem}.words.json').write_text(json.dumps(words, indent=1))
    Path(f'{stem}.txt').write_text(''.join(f"[{s['start']:.2f}-{s['end']:.2f}] {s['text']}\n" for s in sentences))
    print(f'{len(words)} words, {len(sentences)} sentences -> {stem}.words.json, {stem}.txt')


if __name__ == '__main__':
    main()
