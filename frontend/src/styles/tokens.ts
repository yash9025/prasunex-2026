/**
 * Bridge at Night Design System Tokens
 * Per Specification Section 14.1
 */

export const tokens = {
  colors: {
    // Canvas & Surfaces
    navy: '#0B1020',          // Primary dark background canvas
    indigo: '#151B3A',        // Card, container & modal surface
    indigoElevated: '#1A2248',// Elevated cards and hovers
    border: '#27325E',        // Primary structural border
    borderSubtle: '#1E2752',  // Subtle dividers

    // Pedagogical Semantic Accents
    violet: '#7C5CFF',        // Primary actions, brand identity, student creation
    cyan: '#22D3EE',          // System diagnostic evidence, automated signals
    amber: '#FFB547',         // Teacher pedagogical decisions, pending confirmations
    mint: '#34D399',          // Validated states, mastery achieved, verified arithmetic
    coral: '#FF6B6B',         // Errors, dismissals, unvalidated states, severe gaps

    // High-Contrast Typography
    lightRelief: '#F6F3EC',   // Primary text (exceeds WCAG AAA contrast on canvas)
    textMuted: '#94A3B8',     // Secondary supportive text (WCAG AA compliant)
    textDim: '#64748B',       // Metadata and tertiary timestamps
  },

  typography: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Calibri, Roboto, "Helvetica Neue", sans-serif',
    codeFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace',
  },

  shadows: {
    sm: '0 2px 4px rgba(0, 0, 0, 0.2)',
    md: '0 8px 16px -4px rgba(0, 0, 0, 0.4)',
    lg: '0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5)',
    xl: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
    glowViolet: '0 0 20px rgba(124, 92, 255, 0.35)',
    glowCyan: '0 0 20px rgba(34, 211, 238, 0.35)',
    glowMint: '0 0 20px rgba(52, 211, 153, 0.35)',
  },

  radii: {
    sm: '6px',
    md: '10px',
    lg: '14px',
    full: '9999px',
  },
} as const;
