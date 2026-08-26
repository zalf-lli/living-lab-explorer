import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { COLORS, FONT_FAMILY } from "../theme";

/**
 * Full-bleed placeholder used when a scene's clip hasn't been captured yet, so the Studio and
 * renders never break on a missing video file while the capture pipeline is catching up.
 */
export const TitleCard: React.FC<{ title: string; subtitle?: string }> = ({
  title,
  subtitle,
}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill
      style={{
        background: COLORS.bg,
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div style={{ opacity, textAlign: "center", fontFamily: FONT_FAMILY }}>
        <div style={{ fontSize: 84, fontWeight: 700, color: COLORS.teal }}>
          {title}
        </div>
        {subtitle ? (
          <div style={{ fontSize: 32, marginTop: 16, color: COLORS.tealMid }}>
            {subtitle}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
