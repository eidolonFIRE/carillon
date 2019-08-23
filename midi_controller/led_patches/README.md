# Usage
Patches/commands are seperated by semi-colon.

`cmd/patch [flags] [colors];`
Flags are listed below for each patch.
Colors are provided in this format `(0,128,255)`. The numbers represent red, green, blue channels with `0` value being off and `255` being full bright.

Example:
```python
  clear; # stop all previously running patches so we can start a new set
  fade; # will fade to off by default
  simple hold C4:G4 red; # notes played from C4 to G4 will hold red color as long as note held.
  gradient G4:C6 rainbow; # notes played from G4 to C6 will sample the rainbow and only set the color initially when the note is played.
```

# LED patches/commands

### `clear`
  Stops all running patches. By default, leds will now fade off.

### `fade` 
_Slowly changes the color of all the bells._
```
  - range   : Limit patch to note range.
  - random  : Choses a random color to fade the bell to. When the color is reached, a new target color is chosen.
  - rainbow : Fade all to a rainbow pattern.
  - rate    : Fade rate. `1.0` is fade instantly, `0.0` is don't fade at all. _(float from 0.0 to 1.0)_
  - <colors>: If `rainbow` flag is not given, the first color provided will be used. If no color given, 
```

### `simple`
_Light up bell when note played._
```
  - hold    : Keep LED at color until note released.
  - range   : Limit patch to note range.
  - random  : If no color is provided, use random color per note event, otherwise choose randomly from colors provided.
  - rainbow : Color for any note is slowly cycled through the rainbow.
  - all     : Apply color to all bells regardless of note played.
  - <colors>: Cycle through colors provided. (use `random` flag to sample randomly instead of cycling sequentially)
```

### `gradient`
_Color chosen from gradient based on note value._
```
  - hold    : Keep LED at color until note released.
  - range   : Limit patch to note range.
  - random  : Instead of using note value, randomly sample gradient.
  - <colors>: Colors are put in gradient and spaced equally.
```

### `spin`
_Spin colors around inside bell._
```
  - range   : Limit patch to note range.
  - rate    : How fast to initially spin. _(float from 0.0 to 1.0)_
  - rainbow : Use red, green, blue as `colors`.
  - <colors>: Three colors must be specified. 
```
