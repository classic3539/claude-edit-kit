# Claude edit kit

Edit your videos with Claude Code. Claude builds the edit as code with HyperFrames, cuts from a word-by-word transcript, and a separate checker agent reviews every render against numbers measured from edits you want to copy.

Needs: a Mac (Apple Silicon for the included transcriber) and Claude Code.

## Setup (once)

```bash
git clone https://github.com/classic3539/claude-edit-kit
cd claude-edit-kit
./setup.sh
```

`setup.sh` installs ffmpeg, yt-dlp, Node, a local transcriber and the two Claude plugins (HyperFrames for editing, Watch so Claude can see videos). If it says Homebrew is missing, install it from https://brew.sh and run `./setup.sh` again.

## Use it

Open Claude Code in this folder:

```bash
claude
```

1. **Set your style.** Paste 3 to 5 links to edits you want yours to look like and say: *make my style from these*. Claude measures them (shot length, cuts per minute, pauses, loudness, captions) and writes `STYLE.md`. Pick few, pick well: more references just average into nothing.
2. **Edit.** Drop raw footage in `footage/` and say: *edit footage/my-clip.mov*. Claude transcribes it, cuts from the transcript, builds it, renders to `renders/`, and the checker reviews it, for up to 3 fix rounds.
3. **Watch it yourself.** You're the final judge, not Claude. When you give notes that apply to every video, tell Claude to add them to `STYLE.md`.

## What's in here

- `CLAUDE.md` is the instructions Claude follows (setup, style, edit loop).
- `.claude/agents/edit-checker.md` is the reviewer. It never edits, only checks.
- `scripts/transcribe.py` gives word-level timestamps, chunked so long audio doesn't run a 16 GB Mac out of memory.
- `scripts/measure.py` is the same ruler for references and your renders: shot length, cuts per minute, frozen and black frames, dead air, loudness, plus frames to look at.
- `STYLE.template.md` is what `STYLE.md` gets filled from.
