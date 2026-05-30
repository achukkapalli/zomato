---
name: Zomoto
colors:
  surface: '#fff8f7'
  surface-dim: '#f0d3d2'
  surface-bright: '#fff8f7'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#fff0ef'
  surface-container: '#ffe9e8'
  surface-container-high: '#ffe1e0'
  surface-container-highest: '#f9dcda'
  on-surface: '#271717'
  on-surface-variant: '#5b403f'
  inverse-surface: '#3e2c2b'
  inverse-on-surface: '#ffedeb'
  outline: '#8f6f6e'
  outline-variant: '#e4bebc'
  surface-tint: '#bb162c'
  primary: '#b7122a'
  on-primary: '#ffffff'
  primary-container: '#db313f'
  on-primary-container: '#fffbff'
  inverse-primary: '#ffb3b1'
  secondary: '#006492'
  on-secondary: '#ffffff'
  secondary-container: '#58bcfd'
  on-secondary-container: '#004a6d'
  tertiary: '#006762'
  on-tertiary: '#ffffff'
  tertiary-container: '#00837c'
  on-tertiary-container: '#f3fffd'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ffdad8'
  primary-fixed-dim: '#ffb3b1'
  on-primary-fixed: '#410007'
  on-primary-fixed-variant: '#92001c'
  secondary-fixed: '#cae6ff'
  secondary-fixed-dim: '#8ccdff'
  on-secondary-fixed: '#001e2f'
  on-secondary-fixed-variant: '#004b6f'
  tertiary-fixed: '#8ef4eb'
  tertiary-fixed-dim: '#71d7cf'
  on-tertiary-fixed: '#00201e'
  on-tertiary-fixed-variant: '#00504c'
  background: '#fff8f7'
  on-background: '#271717'
  surface-variant: '#f9dcda'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 34px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-bold:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
  price-display:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  container-margin: 16px
  gutter: 16px
---

## Brand & Style

The design system is engineered for the high-velocity world of food technology, prioritizing immediate clarity, appetizing aesthetics, and effortless navigation. The brand personality is energetic yet dependable, acting as a sophisticated bridge between local culinary craft and modern logistics.

The visual style follows a **Corporate / Modern** aesthetic with a strong emphasis on **Minimalism**. It utilizes generous whitespace to reduce cognitive load during the decision-making process. The interface relies on a "Card-First" architecture, using subtle depth to organize information hierarchy and high-quality typography to ensure legibility across diverse lighting conditions (e.g., ordering on the go). The goal is to evoke a sense of freshness, reliability, and speed.

## Colors

The palette is anchored by a **Warm Red/Coral** primary color, chosen to stimulate appetite and signify urgency and passion. This is balanced by a **Soft Teal** for secondary utility actions and informational highlights, ensuring the UI doesn't feel overly aggressive. 

The background strategy utilizes "Paper on Smoke"—pure white surfaces over very light off-white foundations—to create natural separation without the need for heavy borders. The **Soft Green** is reserved strictly for positive states such as "Open Now," "Veg," or "Payment Successful."

## Typography

This design system utilizes **Inter** for its exceptional legibility and systematic feel. The type hierarchy is strictly enforced to guide users through restaurant menus and checkout flows.

- **Display & Headlines:** Use tighter letter-spacing and heavier weights to create a strong visual anchor for restaurant names and section headers.
- **Body Text:** Optimized for readability with a comfortable line height. 
- **Price & Currency:** The currency symbol (₹) should always match the weight of the adjacent price value but may be scaled down to 80% size to keep the numerical value as the primary focus.
- **Labels:** Used for metadata like "45 mins" or "Free Delivery," utilizing uppercase and increased letter spacing for quick scanning.

## Layout & Spacing

The layout utilizes a **12-column fluid grid** for desktop and a **4-column grid** for mobile. A strict 4px baseline grid ensures vertical rhythm.

- **Mobile Layout:** 16px side margins are mandatory. Content cards should span the full width of the margins.
- **Desktop Layout:** Maximum container width of 1200px, centered.
- **Component Spacing:** Use 16px (md) for internal card padding and 24px (lg) to separate distinct sections of the page.

## Elevation & Depth

Visual hierarchy is achieved through **Ambient Shadows** and **Tonal Layers**. Shadows are used sparingly to indicate interactivity and importance.

- **Level 0 (Floor):** Neutral off-white (#F8F8F8). Used for the main background.
- **Level 1 (Cards):** Pure white surface with a very soft, diffused shadow (Y: 2, Blur: 8, Color: RGBA(0,0,0,0.05)).
- **Level 2 (Hover/Active):** Slightly more pronounced shadow (Y: 4, Blur: 12, Color: RGBA(0,0,0,0.08)) to indicate the card is liftable.
- **Level 3 (Sticky Headers/Modals):** High-diffusion shadow with a subtle tint of the primary color in the shadow mix to maintain brand warmth.

## Shapes

The shape language is friendly and modern. A **Rounded** strategy is applied across all components to soften the technical nature of the app.

- **Small Components (Buttons, Inputs):** Use a 12px (radius-md) corner radius.
- **Large Components (Restaurant Cards, Banners):** Use a 16px (radius-lg) corner radius.
- **Selection Indicators:** Use pill-shapes (fully rounded) for filters and status chips to distinguish them from actionable buttons.

## Components

### Buttons
- **Primary:** Warm Red background, White text. High-contrast, 12px radius.
- **Secondary:** White background, Warm Red border (1px) and text.
- **Ghost:** Soft Teal text, no background. Used for "View Menu" or "More Details."

### Cards
- **Restaurant Card:** 16px corner radius, Level 1 elevation. Image at top with 0px top-radius (masked by card container). Padding of 16px for content below image.
- **Rating Badge:** Small green pill with a white star icon and text. Font size: 12px (label-bold).

### Inputs & Search
- **Location Pin:** Always rendered in Warm Red (#E23744) to signify the "Current Point."
- **Search Bar:** Large, 12px radius, light gray background (#F0F0F0) or Level 1 elevation with a search icon prefix.
- **Currency (₹):** Inlined within price components, using the `price-display` token.

### Chips & Feedback
- **Filters:** Pill-shaped, 8px vertical padding, 16px horizontal. Unselected: Gray border. Selected: Primary Red background or border.
- **Star Ratings:** 5-star scale. Active stars in Gold (#FFC107), inactive in light gray.