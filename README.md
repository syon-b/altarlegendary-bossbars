# AltarLegendary Boss Bars

A small resource pack that adds themed boss-bar frames for the five legendary-dungeon bosses on our server:
**The Fallen Knight**, **The Quarry Breaker**, **Captain Blackmarrow**, **The Heretic Bishop** and **The Hollow Matriarch**.

![preview](preview.png)

## Download

**[⬇ Download AltarLegendaryBossBars.zip](https://github.com/syon-b/altarlegendary-bossbars/releases/latest/download/AltarLegendaryBossBars.zip)**

- Minecraft Java **26.1 – 26.3**
- Normally the server sends it to you automatically when you join. If you want to install it yourself: put the zip in
  `.minecraft/resourcepacks/` and enable it in *Options → Resource Packs*.
- Only adds its own font + textures (namespace `altarlegendary`), so it works alongside any other pack
  (including other boss-bar packs). Without it you just see the normal boss bar.

## Server owners

Set this in `plugins/AltarLegendaryWH/structures.yml`:

```yaml
structures:
  resource-pack:
    url: "https://github.com/syon-b/altarlegendary-bossbars/releases/latest/download/AltarLegendaryBossBars.zip"
```

## How it works

Each frame is a font glyph (`altarlegendary:bossbars`, ``–``) drawn over the vanilla bar; the plugin uses
it as the boss bar title for players who have the pack. `make_bossbar_pack.py` regenerates the pack (needs Pillow).

All artwork is original.
