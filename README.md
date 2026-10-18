# Nanoleaf for Home Assistant

Local-only Home Assistant integration for Nanoleaf lights, with a few bundled scenes of our own.

- Essentials bulbs and lightstrips (the Matter generation) as well as panels, Canvas, Shapes, Elements and Lines
- Everything over the local OpenAPI - no cloud, no Nanoleaf account
- Effects as a native light effect list
- Bundled scenes (Moonlight, Ember, Deep Sea) that install themselves onto the strip, so they keep working from any controller

Forked and trimmed from [loebi-ch/nanoleaf](https://github.com/loebi-ch/nanoleaf) (MIT), which wraps [aionanoleaf2](https://github.com/loebi-ch/aionanoleaf2). We keep the dependency current and add our own scenes.

## Install

HACS > Integrations > ⋮ > Custom repositories > `trash-panda-v91-beta/hass-nanoleaf` (category: Integration), install **Nanoleaf**, restart Home Assistant.

## Pair a device

1. Make sure the device is on your WiFi (set it up in the Nanoleaf app once if needed).
2. Add the integration in Home Assistant and enter the device host.
3. When asked for a token: open the device settings in the Nanoleaf app, tap **Connect to API**, and submit within 30 seconds. (Panel devices without app support: hold the power button for 5 seconds until the LEDs flash instead.)

The token is stored in the config entry. Devices can stay in the Nanoleaf app or not - the API works either way, and removing the device from the app keeps the token valid. A factory reset is the only thing that wipes it.

## Scenes

The bundled scenes appear in the effect list next to the device's own effects. Picking one for the first time saves it on the strip (via the API `add` command) and starts it. Add more presets in `custom_components/nanoleaf/scenes.py` - each is a palette and a speed over the standard color-flow motion.

New scenes can also be created at runtime with the `nanoleaf.add_scene` service - no app needed. Give a light, a name, a hex palette (2+ colors; two colors become a smooth gradient), and optionally a motion style - the movement engines behind the built-in scenes (flow, wave, glow, scatter, pulse, ufo, twinkle, flash). The scene is saved on the strip and shows up in the effect list immediately:

```yaml
action: nanoleaf.add_scene
data:
  entity_id: light.nanoleaf_iml_a2d
  name: Northern Glow
  colors: ["0D1B2A", "415A77", "FFFFFF"]
  motion: wave
  trans_time: 45
```

Scenes are removed with `nanoleaf.remove_scene` (same `entity_id` + `name`), no app needed.

## Development

```bash
uv sync --all-groups   # dev environment
mise run check         # all linters
mise run fix           # auto-fix
mise run test          # tests
```
