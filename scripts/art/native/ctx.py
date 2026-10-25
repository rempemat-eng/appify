"""The render context: the density, the biome and the plan every painter reads.

Density is a render parameter, never stored in plan data (rules-system.md 5). The painters
compute their size tables when they are imported (the c-tiles sheets, the face sheet, the lip
profiles), so a process renders at one density: `configure` is called once, before the
painters are imported (`build.py` does this).

    from scripts.art.native import ctx
    ctx.configure(2.0, biome, plan)
    from scripts.art.native import compose      # the painters now draw at density 2

D   art px (texels) per world px
TT  one 16 world px terrain tile in texels
P   a size in world px as whole texels at this density (at least lo)
F   a size in world px as a float at this density
"""
from __future__ import annotations

D = 2.0
TT = 32
BIOME: dict = {}
PLAN: dict = {}
_configured = False


def configure(density: float, biome: dict | None = None, plan: dict | None = None) -> None:
    global D, TT, _configured
    if _configured and density != D:
        raise RuntimeError('one density per process: the painters are already sized for %g' % D)
    D = float(density)
    TT = int(round(16 * D))
    if biome is not None:
        BIOME.clear()
        BIOME.update(biome)
    if plan is not None:
        PLAN.clear()
        PLAN.update(plan)
    _configured = True


def P(v, lo=1):
    """A size in world px as whole art px at this density (at least lo)."""
    return max(lo, int(round(v * D)))


def F(v):
    return v * D
