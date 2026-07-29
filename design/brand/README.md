# EZ Brand — the non-negotiable source of truth

Everything we design follows **EZ Brand Guidelines 2.0**. No deviation.

- **`EZ_Brand_Guidelines_2.0.pptx`** — the original deck (authoritative).
- **`ez.brand.tokens.json`** — machine-readable extraction: exact colours, type, and the UI role mapping.

> If any other token file, mockup, or prototype disagrees with this folder, **this folder wins**.

## Colour

### Primary
| Swatch | Hex | RGB | Use |
|---|---|---|---|
| EZ Orange | `#EA7B2C` | 234, 123, 44 | **The brand colour.** Primary actions, brand marks, key accents |
| Charcoal | `#3D3D3D` | 61, 61, 61 | Primary neutral — body text, UI ink |
| Sky | `#3CC3F2` | 60, 195, 242 | Information, links, secondary emphasis |
| Gold | `#F1B715` | 241, 183, 21 | Attention, warning, highlight |

### Secondary
| Swatch | Hex | RGB | Use |
|---|---|---|---|
| Maroon | `#901918` | 144, 25, 24 | Critical, error, at-risk |
| Navy | `#112949` | 14, 41, 73 | Deep ground, headers, dark surfaces |
| Forest | `#0A351F` | 10, 53, 31 | Success, verified, positive |
| Peach | `#EDA27C` | 237, 162, 124 | Soft orange support, tints |

Theme scheme as authored in the deck: `dk1 #0E2949` · `lt1 #FFFFFF` · `dk2 #3D3D3D` · `lt2 #FFFFFF` · `accent1 #EA7B2C` · `accent2 #EDA27C` · `accent3 #3CC3F2` · `accent4 #901918` · `accent5 #F1B715` · `accent6 #0A351F`.

## Typography

- **Exo 2.0** — the EZ typeface. Theme **major and minor**, so it carries headings, UI and body.
  `'Exo 2.0', 'Exo 2', 'Exo', system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif`
- **Cambria** — secondary. Editorial, long-form, quotations.
  `Cambria, Georgia, 'Times New Roman', serif`

## Brand image & values

**Image:** Consistently High-Quality · Round the Clock Availability · Faster than the Fastest
**Values:** Innovating with AI · People First

## Applying it

Use `uiMapping` in `ez.brand.tokens.json` for product surfaces — it maps the brand palette onto UI roles (brand / ink / info / good / warn / crit and their soft + ink variants) so every WS 3.0 screen reads as EZ without re-deriving colours per screen.
