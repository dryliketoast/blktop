# Renders docs/demo.gif.  Run from the repo root:  vhs docs/demo.tape
# Assumes `blktop` is on PATH, some disk I/O is happening, and a throwaway
# HOME so your own ~/.config/blktop/config.json is left alone.
Output docs/demo.gif
Set Shell "bash"
Set FontSize 18
Set Width 1200
Set Height 600
Set Padding 12
Set TypingSpeed 60ms

Type "blktop --theme dracula" Enter
Sleep 9s
Type "b" Sleep 3s
Type "b" Sleep 2s
Type "t" Sleep 1500ms
Type "t" Sleep 1500ms
Type "t" Sleep 1500ms
Type "t" Sleep 3s
Type "q" Sleep 1s
