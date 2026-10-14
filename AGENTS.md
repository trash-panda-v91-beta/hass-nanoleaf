# hass-nanoleaf

Home Assistant custom integration for Nanoleaf lights (HACS). Python 3.14, dev tooling via mise + uv.

## Layout

- `custom_components/nanoleaf/` - the integration. `light.py` is the device surface, `scenes.py` holds the bundled scenes, `config_flow.py` handles pairing (host + API token).
- `tests/unit/` - pytest checks. Keep tests dependency-light: no Home Assistant objects in unit tests.
- `hk.pkl` / `ruff.toml` / `.rumdl.toml` - lint and format rules shared with the other repos.

## Commands

```bash
mise run check   # lint everything
mise run fix     # fix what can be fixed
mise run test    # pytest
uv sync --all-groups
```

## Notes

- The device API is the Nanoleaf OpenAPI (port 16021, mDNS `_nanoleafapi._tcp`). Docs: "Nanoleaf Matter WiFi Essentials Open API" in the Nanoleaf developer wiki.
- Scenes are pushed onto the device itself with the effects `add` command; they live in the device's effect list afterwards.
- `scenes.py` uses `aionanoleaf2`'s private `_request` hook - the library has no public method for adding effects. Revisit when upstream adds one.
- Keep the code minimal and typed. Prefer deleting over wrapping.
