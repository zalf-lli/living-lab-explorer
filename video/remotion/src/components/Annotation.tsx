import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { HEIGHT, WIDTH, type Annotation as AnnotationType } from "../scenes";
import { COLORS, FONT_FAMILY } from "../theme";

const GAP = 14; // distance between the highlight box and its caption
const PAD = 10; // how far the highlight sits outside the element's own bounds
const MARGIN = 24; // minimum clearance between a caption and the frame edge

/**
 * Draws a highlight around a real UI element (its rect measured during capture) plus a caption
 * tethered to it, so the text sits next to whatever it describes instead of floating in a corner.
 * `place: "note"` skips the highlight entirely and renders a plain centred caption.
 */
export const Annotation: React.FC<{
  annotation: AnnotationType;
  text: string;
}> = ({ annotation, text }) => {
  const frame = useCurrentFrame();
  const { durationInFrames, rect, place } = annotation;

  const appear = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: "clamp",
  });
  const disappear = interpolate(
    frame,
    [Math.max(durationInFrames - 12, 0), durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
  const opacity = Math.min(appear, disappear);

  const label = (
    <div
      style={{
        fontFamily: FONT_FAMILY,
        fontSize: 26,
        fontWeight: 700,
        lineHeight: 1.25,
        color: COLORS.teal,
        background: COLORS.white,
        border: `1.5px solid ${COLORS.mutedLight}`,
        borderLeft: `4px solid ${COLORS.orange}`,
        borderRadius: 10,
        padding: "12px 18px",
        boxShadow: "0 6px 18px rgba(0, 65, 63, 0.16)",
        whiteSpace: "nowrap",
      }}
    >
      {text}
    </div>
  );

  if (place === "note") {
    const rise = interpolate(frame, [0, 12], [10, 0], {
      extrapolateRight: "clamp",
    });
    return (
      <AbsoluteFill
        style={{
          alignItems: "center",
          justifyContent: "flex-end",
          paddingBottom: 76,
          opacity,
        }}
      >
        <div style={{ transform: `translateY(${rise}px)` }}>{label}</div>
      </AbsoluteFill>
    );
  }

  const box = {
    left: rect.x - PAD,
    top: rect.y - PAD,
    width: rect.width + PAD * 2,
    height: rect.height + PAD * 2,
  };

  // Rough caption width, used only to decide which side/edge to anchor to. Text is nowrap at a
  // known size, so character count estimates it closely enough to keep the box inside the frame.
  const estWidth = text.length * 13.5 + 44;

  // Captions anchor to whichever edge of the highlight keeps them on screen, rather than always
  // centring: many of the annotated controls (language toggle, contact button, partners tab) sit
  // hard against the right edge, where a centred caption would run off the frame.
  const captionStyle: React.CSSProperties = { position: "absolute" };
  const anchorHorizontally = () => {
    if (box.left + box.width / 2 > WIDTH / 2) {
      captionStyle.right = Math.max(MARGIN, WIDTH - (box.left + box.width));
    } else {
      captionStyle.left = Math.max(MARGIN, box.left);
    }
  };

  if (place === "inside") {
    captionStyle.left = box.left + box.width / 2;
    captionStyle.top = box.top + box.height / 2;
    captionStyle.transform = "translate(-50%, -50%)";
  } else if (place === "above") {
    anchorHorizontally();
    captionStyle.top = box.top - GAP;
    captionStyle.transform = "translateY(-100%)";
  } else if (place === "left" || place === "right") {
    captionStyle.top = box.top + box.height / 2;
    captionStyle.transform = "translateY(-50%)";
    // Flip to the other side when the preferred one has no room left in frame.
    const fitsRight = box.left + box.width + GAP + estWidth <= WIDTH - MARGIN;
    const fitsLeft = box.left - GAP - estWidth >= MARGIN;
    const useRight = place === "right" ? fitsRight || !fitsLeft : !fitsLeft && fitsRight;
    if (useRight) {
      captionStyle.left = box.left + box.width + GAP;
    } else {
      captionStyle.right = Math.max(MARGIN, WIDTH - box.left + GAP);
    }
  } else {
    anchorHorizontally();
    captionStyle.top = box.top + box.height + GAP;
  }

  // A highlight that would run off-screen reads as a bug; nudge it back inside the frame.
  const clampedLeft = Math.max(0, Math.min(box.left, WIDTH - box.width));
  const clampedTop = Math.max(0, Math.min(box.top, HEIGHT - box.height));

  return (
    <AbsoluteFill style={{ opacity }}>
      <div
        style={{
          position: "absolute",
          left: clampedLeft,
          top: clampedTop,
          width: box.width,
          height: box.height,
          border: `2.5px solid ${COLORS.orange}`,
          borderRadius: 12,
          boxShadow: `0 0 0 4px rgba(235, 91, 37, 0.14)`,
          pointerEvents: "none",
        }}
      />
      <div style={captionStyle}>{label}</div>
    </AbsoluteFill>
  );
};
