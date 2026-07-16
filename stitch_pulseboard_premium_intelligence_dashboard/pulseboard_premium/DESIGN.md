---
name: PulseBoard Premium
colors:
  surface: '#131318'
  surface-dim: '#131318'
  surface-bright: '#39383e'
  surface-container-lowest: '#0e0e13'
  surface-container-low: '#1b1b20'
  surface-container: '#1f1f24'
  surface-container-high: '#2a292f'
  surface-container-highest: '#35343a'
  on-surface: '#e4e1e9'
  on-surface-variant: '#ccc3d8'
  inverse-surface: '#e4e1e9'
  inverse-on-surface: '#303036'
  outline: '#958da1'
  outline-variant: '#4a4455'
  surface-tint: '#d2bbff'
  primary: '#d2bbff'
  on-primary: '#3f008e'
  primary-container: '#7c3aed'
  on-primary-container: '#ede0ff'
  inverse-primary: '#732ee4'
  secondary: '#cebdff'
  on-secondary: '#381385'
  secondary-container: '#4f319c'
  on-secondary-container: '#bea8ff'
  tertiary: '#45dfa4'
  on-tertiary: '#003825'
  tertiary-container: '#007551'
  on-tertiary-container: '#6bffc1'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#eaddff'
  primary-fixed-dim: '#d2bbff'
  on-primary-fixed: '#25005a'
  on-primary-fixed-variant: '#5a00c6'
  secondary-fixed: '#e8ddff'
  secondary-fixed-dim: '#cebdff'
  on-secondary-fixed: '#21005e'
  on-secondary-fixed-variant: '#4f319c'
  tertiary-fixed: '#68fcbf'
  tertiary-fixed-dim: '#45dfa4'
  on-tertiary-fixed: '#002114'
  on-tertiary-fixed-variant: '#005137'
  background: '#131318'
  on-background: '#e4e1e9'
  surface-variant: '#35343a'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 34px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 30px
    letterSpacing: -0.02em
  body-md:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 24px
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.08em
  metric-xl:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
  metric-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base-grid: 8px
  card-padding: 24px
  section-padding: 32px
  gutter: 16px
  container-max: 1440px
---

## Brand & Style
The design system is engineered for elite financial intelligence, blending high-density data visualization with an elegant, high-end aesthetic. It draws inspiration from modern technical platforms, utilizing a "Dark Mode First" philosophy to reduce eye strain during deep analytical sessions.

The style is a hybrid of **Minimalism** and **Glassmorphism**, characterized by a deep obsidian canvas, subtle inner-border light leaks, and sophisticated atmospheric glows. The emotional response is one of precision, authority, and technological edge—evoking the feeling of a private trading floor or a premium command center.

## Colors
The palette is rooted in a "Near-Black" spectrum to provide maximum contrast for data points. 

- **Canvas & Surfaces:** The background uses a layered dark architecture. `#0B0B10` serves as the base, while `#141420` and `#1A1A28` create physical hierarchy for sidebars and content cards.
- **The Signature Gradient:** A vivid transition from Purple (#7C3AED) to Violet (#A78BFA) is reserved for high-intent actions, active navigation states, and subtle "glow" effects behind key metrics.
- **Functional Accents:** Mint Green, Amber, and Rose are utilized strictly for semantic status (Positive/Neutral/Negative). These colors should include a low-opacity "soft glow" (drop shadow) when representing live data updates to signal vitality.

## Typography
This design system uses **Inter** exclusively to maintain a clean, technical appearance. 

- **Hierarchy:** Titles use semi-bold weights with tight tracking (-0.02em) to feel compact and authoritative. 
- **Data Integrity:** All numerical values, specifically in tables and dashboards, must use **Tabular Numerals** (`tnum`) to ensure columns of figures align perfectly, facilitating easier scanning of financial data.
- **Meta Information:** Labels use uppercase styling with increased letter spacing (0.08em) and a muted color palette to distinguish them from actionable content.

## Layout & Spacing
The system operates on a rigorous **8pt grid**. 

- **Layout Model:** A fluid 12-column grid for desktop with 24px gutters. On tablet, this scales to 8 columns, and on mobile, it collapses to a single column with 16px margins.
- **Density:** High-density data views should prioritize 24px padding within cards to maximize information display while maintaining a premium, "breathable" feel.
- **Top Bars:** Use a fixed height (64px) with a backdrop-blur effect (20px) to allow content to scroll underneath while maintaining legibility.

## Elevation & Depth
Depth is created through "layered glass" rather than traditional heavy shadows.

- **Internal Borders:** Every card and surface element must feature a 1px inner border (`rgba(255,255,255,0.06)`). This simulates a subtle light catch on the "edge" of the glass.
- **Backdrop Blur:** Navigation bars and modal overlays utilize a 20px-30px Gaussian blur.
- **Featured Elevation:** For high-priority elements (e.g., a "Pro" feature or a highlighted trade), use a **gradient border**. This is achieved by a 1px outer stroke that transitions from Purple to Violet, accompanied by a very soft, low-opacity glow of the same color.

## Shapes
The shape language combines the approachability of large radii with the precision of smaller functional components.

- **Containers:** Large surface containers and dashboard cards use a prominent **20px radius**, creating a soft, premium frame for the data.
- **Interactive Elements:** Buttons, input fields, and chips use a more structured **8px radius** to feel tool-like and efficient.
- **Icons:** Use 1.5px stroke width for icons, avoiding filled styles except for active states.

## Components
- **Buttons:** Primary buttons feature the Signature Gradient background with white text. Secondary buttons are "Ghost" style with a 1px border (`rgba(255,255,255,0.1)`) and a subtle hover fill.
- **Input Fields:** Backgrounds should be 5% lighter than the surface they sit on. Use the Primary Purple for the focus border state, accompanied by a 4px soft outer glow.
- **Cards:** Cards should be defined by the `#1A1A28` background and the 1px internal border. For hover states, increase the border opacity to `0.12`.
- **Chips/Badges:** Small, 8px radius. Use semantic background tints (e.g., Mint Green at 10% opacity) with high-contrast text of the same hue.
- **Lists:** Data rows should be separated by a 1px line (`rgba(255,255,255,0.04)`). On hover, the entire row should transition to a slightly lighter surface color.
- **Charts:** Use a custom theme for charts where the line/bar uses the Signature Gradient or semantic accents, and grid lines are kept at a minimal `rgba(255,255,255,0.02)`.