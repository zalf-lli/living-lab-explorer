import { AbsoluteFill, Img, Series, interpolate, staticFile, useCurrentFrame } from "remotion";
import { REPORT_PAGE_FRAMES } from "../scenes";
import { COLORS } from "../theme";

// Pages are rendered at 1920px wide and are much taller than the frame, so each one is panned
// down its own length rather than shrunk to fit — the KPI tiles and map stay legible.
const PAGE_WIDTH = 1180;

const Page: React.FC<{ src: string }> = ({ src }) => {
  const frame = useCurrentFrame();
  const travel = interpolate(frame, [0, REPORT_PAGE_FRAMES], [0, -620], {
    extrapolateRight: "clamp",
  });
  const opacity = interpolate(
    frame,
    [0, 10, REPORT_PAGE_FRAMES - 10, REPORT_PAGE_FRAMES],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
  return (
    // Light backdrop, not a dark one: cutting from the bright app UI to a dark page and back
    // registered as two hard luminance jumps in the assembled video — exactly the kind of flash
    // the scene trimming was introduced to remove.
    <AbsoluteFill
      style={{
        background: COLORS.bg,
        alignItems: "center",
        justifyContent: "flex-start",
        overflow: "hidden",
      }}
    >
      <div style={{ opacity, transform: `translateY(${travel}px)`, marginTop: 40 }}>
        <Img
          src={src}
          style={{
            width: PAGE_WIDTH,
            border: `1px solid ${COLORS.mutedLight}`,
            boxShadow: "0 18px 44px rgba(0, 65, 63, 0.18)",
            borderRadius: 4,
          }}
        />
      </div>
    </AbsoluteFill>
  );
};

/** Scrolling series of the downloaded PDF's thematic pages, rendered from captured PNGs. */
export const ReportScroll: React.FC<{ lang: string; files: string[] }> = ({
  lang,
  files,
}) => {
  return (
    <Series>
      {files.map((file) => (
        <Series.Sequence key={file} durationInFrames={REPORT_PAGE_FRAMES}>
          <Page src={staticFile(`captured/report-pages/${lang}/${file}`)} />
        </Series.Sequence>
      ))}
    </Series>
  );
};
