// Lifted verbatim from the app's own palette (app/src/theme.js) so the video's annotations read
// as part of the product rather than as a separate overlay layer. Satoshi isn't bundled as a font
// file in the repo, so the stack falls through to system-ui in the render, matching how the app
// itself renders here.
export const COLORS = {
  white: "#ffffff",
  bg: "#f9fef9",
  orange: "#eb5b25",
  orangeDark: "#dc4b14",
  teal: "#005754",
  tealMid: "#008581",
  tealBg: "#00413f",
  greenMid: "#359269",
  mutedLight: "#c3e9d8",
};

export const FONT_FAMILY = "'Satoshi', system-ui, sans-serif";
