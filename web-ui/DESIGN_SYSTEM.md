# EduSynth Technical Design System: Midnight Obsidian (ID: 25-26J-130)

This architectural document defines the "Midnight Obsidian" design system for EduSynth, achieving a neutral, ultra-professional dark environment by eliminating all blue/purple background tints.

## 1. Primary Palette (Obsidian & Aqua)
The neutral-core identity for agentic orchestration.

| Identity | HEX Code | Usage |
| :--- | :--- | :--- |
| **AGENTIC CORE** (Primary) | `#0077B6` | Core actions and primary CTAs |
| **OBSIDIAN BASE** (Background) | `#121212` | Absolute neutral dark background |
| **SLATE SURFACE** (Glass) | `#1E293B` | Semi-transparent layering (**15% opacity**) |
| **INTERFACE BORDERS** (Frosted) | `#90E0EF` | 1px strokes (10% opacity in dark) |
| **NAVBAR BORDER** (Indigo) | `#6366F1` | 1px indigo border (**20% opacity**) |

## 2. Semantic Signals
- **SUCCESS / MASTERY**: `#00AFB9` (Seafoam)
- **ALERTS / DEVIATION**: `#F07167` (Coral)
- **ACCENT / REASONING**: `#48CAE4` (Sky Aqua)

## 3. Theme Environments

### **Midnight Obsidian (Dark Mode)**
- **Background**: `#121212` (Absolute Dark) - Zero blue/purple base.
- **Surface**: `#1E293B` (Slate) at **15% opacity** for all panels.
- **Navbar**: `#121212` at **70% opacity** with `backdrop-blur-xl` and **#6366F1/20** border.
- **Glass Effect**: `backdrop-blur-3xl` with **1px border @ 10% opacity** (#90E0EF).
- **Text**: `#CAF0F8` (Light Cyan) for maximum contrast against neutral darks.

### **Frosted Coast (Light Mode)**
- **Background**: `#F5FBFE` (Subtle aquatic tint).
- **Surface**: `#FFFFFF` (Pure White).
- **Typography**: `#121212` (Midnight Obsidian).

## 4. Visual Standards
- **Radius**: `20px` (Inner), `40px` (Outer container).
- **Subtlety**: All glass effects are calibrated to 15% opacity to avoid visual noise.
- **Precision**: 3xl-backdrop-blur is mandatory for all layered obsidian surfaces.

## 5. Tailwind Configuration Standard
```javascript
colors: {
  primary: '#0077B6',
  accent: '#48CAE4',
  edu: {
    bg: { dark: '#121212', light: '#F5FBFE' },
    surface: { dark: '#1E293B', light: '#FFFFFF' },
    text: { dark: '#CAF0F8', light: '#121212' }
  }
}
```

---
*Official Style Guide | EduSynth ID: 25-26J-130*
