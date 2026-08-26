import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { INTRO, INTRO_FRAMES } from "../scenes";
import { COLORS, FONT_FAMILY } from "../theme";

// Opening title card. Deliberately not app footage: a flat field of the app's darkest teal, with
// the wordmark set the way Header.jsx sets it (uppercase, heavy, letter-spaced) so the card reads
// as the same product rather than as a generic slide.
export const IntroCard: React.FC = () => {
  const frame = useCurrentFrame();

  const rise = (delay: number) => ({
    opacity: interpolate(frame, [delay, delay + 18], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }),
    transform: `translateY(${interpolate(frame, [delay, delay + 18], [14, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    })}px)`,
  });

  // Everything fades together at the end so the cut into the landing page is clean.
  const outro = interpolate(
    frame,
    [INTRO_FRAMES - 14, INTRO_FRAMES],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <AbsoluteFill
      style={{
        background: COLORS.tealBg,
        alignItems: "center",
        justifyContent: "center",
        fontFamily: FONT_FAMILY,
        opacity: outro,
      }}
    >
      <div style={{ textAlign: "center", maxWidth: 1400 }}>
        <div
          style={{
            ...rise(6),
            fontSize: 44,
            fontWeight: 500,
            color: "rgba(255,255,255,0.82)",
            marginBottom: 22,
          }}
        >
          {INTRO.kicker}
        </div>

        <div
          style={{
            ...rise(16),
            fontSize: 104,
            fontWeight: 900,
            color: COLORS.white,
            textTransform: "uppercase",
            letterSpacing: "6px",
            lineHeight: 1.1,
          }}
        >
          {INTRO.title}
        </div>

        <div
          style={{
            ...rise(26),
            width: 132,
            height: 4,
            background: COLORS.orange,
            borderRadius: 2,
            margin: "40px auto 0",
          }}
        />

        <div
          style={{
            ...rise(38),
            marginTop: 56,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 18,
          }}
        >
          {/* White plate behind the code: scanners need the quiet zone light, and the card's
              background is near-black teal. */}
          <div
            style={{
              background: COLORS.white,
              padding: 18,
              borderRadius: 14,
              lineHeight: 0,
            }}
          >
            <Img
              src={staticFile(INTRO.qrFile)}
              style={{ width: 240, height: 240, display: "block" }}
            />
          </div>
          <div
            style={{
              fontSize: 32,
              fontWeight: 600,
              color: "rgba(255,255,255,0.82)",
            }}
          >
            {INTRO.qrCaption}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
