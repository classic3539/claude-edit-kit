# Claude edit kit

You edit this person's videos. You build edits with HyperFrames (the `/hyperframes` skills), cut from word-level transcripts, and every render is reviewed by the `edit-checker` agent against `STYLE.md`. The person watching is the final judge.

## "Set me up"

1. Run `./setup.sh` and read its output. If Homebrew is missing, tell the person to install it from https://brew.sh (it asks for their password, so it's their step), then run setup again.
2. Check: `ffmpeg -version`, `yt-dlp --version`, `node --version`, `.venv/bin/python -c "import parakeet_mlx"`.
3. Plugins only load in a new session. If `/hyperframes` or `/watch` aren't available, tell the person to quit Claude Code and start it again in this folder.
4. Not an Apple Silicon Mac: parakeet-mlx won't run. Set up whisper.cpp with word-level timestamps and change `scripts/transcribe.py` to call it, keeping the same output files.

## "Make my style from these"

1. Use 3 to 5 references. If they give more, ask which 5 matter most: more references average into nothing.
2. Download each: `yt-dlp -o "references/%(id)s.%(ext)s" <url>`.
3. Measure each: `.venv/bin/python scripts/measure.py references/<file>`.
4. Use `/watch` on each for what numbers can't show: caption look and position, zooms, b-roll, music, what happens in the first 3 seconds.
5. Fill `STYLE.md` from `STYLE.template.md`. Every line is a number or a concrete rule with the range across references. No adjectives. Show the person and fix what they disagree with.

## "Edit footage/<file>"

1. Transcribe: `.venv/bin/python scripts/transcribe.py footage/<file>`. It writes `<file>.words.json` (every word with start and end times) and `<file>.txt` (sentences).
2. Plan the cuts from the transcript: remove filler, false starts, retakes (keep the last good take) and dead air longer than STYLE.md allows. Cut on word boundaries from `words.json`, and leave a short breath (about 0.15 s) before the next word so it doesn't sound chopped. Write the plan to `renders/<name>-cuts.md`: kept lines, removed lines, and why.
3. Build the edit in HyperFrames following STYLE.md. Captions use the exact words that are spoken.
4. Render to `renders/<name>.mp4`.
5. Send the render to the `edit-checker` agent with the paths to STYLE.md, the cut plan and the source transcript.
6. Fix every fail it lists and render again. Stop after 3 rounds. Then hand the render to the person with the checker's last report, naming anything still failing. Never call an edit done while the checker has fails you haven't told them about.
7. When the person gives notes that apply to every video, add them under "Notes from watching" in STYLE.md.

## Rules

- Never modify or delete anything in `footage/`. Work on copies.
- Keep `transcribe.py` chunked (2 minutes). Long audio in one piece can run a 16 GB Mac out of memory and crash it.
- Measure, don't guess. If you claim a render matches STYLE.md, the numbers from `measure.py` back it.
