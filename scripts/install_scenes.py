"""Install the bundled scenes onto a Nanoleaf strip.

Usage: mise run scenes bar   (or: fnox exec -- uv run python scripts/install_scenes.py kir)

Credentials come from fnox (.fnox.toml): NANOLEAF_<NAME>_HOST / NANOLEAF_<NAME>_TOKEN.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from aiohttp import ClientSession
from aionanoleaf2 import Nanoleaf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from custom_components.nanoleaf.scenes import SCENES, install_scene  # noqa: E402


async def main(target: str) -> None:
    """Install every bundled scene on the target strip."""
    prefix = f"NANOLEAF_{target.upper()}"
    async with ClientSession() as session:
        nanoleaf = Nanoleaf(session, os.environ[f"{prefix}_HOST"], os.environ[f"{prefix}_TOKEN"])
        await nanoleaf.get_info()
        print(f"{nanoleaf.name} ({nanoleaf.model}, fw {nanoleaf.firmware_version})")
        for name in SCENES:
            await install_scene(nanoleaf, name, SCENES[name])
            print(f"installed {name}")


if __name__ == "__main__":
    if len(sys.argv) != 2 or (target := sys.argv[1].lower()) not in {"bar", "kir"}:
        sys.exit("usage: install_scenes.py bar|kir")
    asyncio.run(main(target))
