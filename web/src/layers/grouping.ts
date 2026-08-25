import { CONFIG } from "../config/layerConfig";
import {
  MENU,
  THEMES,
  type LegendBlock,
  type MenuEntry,
  type Theme,
} from "../generated/layerRegistry";

/** The group a toggle belongs to. */
export const themeOf = (toggleId: string, generated: Theme): Theme =>
  CONFIG.theme[toggleId] ?? generated;

/** The group a legend block belongs to, found through the layer it explains. */
export function themeOfBlock(block: LegendBlock): Theme {
  const owner =
    block.layer ??
    block.anyOf?.[0] ??
    block.entries?.find((entry) => entry.layer)?.layer;

  return owner ? themeOf(owner, block.theme) : block.theme;
}

/** Groups in display order: the ones named in config first, then the rest. */
export function themesInOrder(): Theme[] {
  const all = Object.keys(THEMES) as Theme[];
  const named = CONFIG.themeOrder.filter((theme) => all.includes(theme));

  return [...named, ...all.filter((theme) => !named.includes(theme))];
}

/** The sidebar menu, with any regrouping applied. */
export function menuByTheme(): Record<Theme, MenuEntry[]> {
  const grouped = Object.fromEntries(
    (Object.keys(THEMES) as Theme[]).map((theme) => [theme, [] as MenuEntry[]]),
  ) as Record<Theme, MenuEntry[]>;

  for (const [theme, entries] of Object.entries(MENU) as [Theme, MenuEntry[]][]) {
    for (const entry of entries) {
      grouped[themeOf(entry.layers[0]?.id ?? "", theme)].push(entry);
    }
  }

  return grouped;
}
