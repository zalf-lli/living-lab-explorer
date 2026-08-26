import { CalculateMetadataFunction, Composition, staticFile } from "remotion";
import { FPS, HEIGHT, INTRO_FRAMES, REPORT_PAGE_FRAMES, WIDTH } from "./scenes";
import { DemoVideo } from "./DemoVideo";
import { fetchManifest, resolveManifest, type ResolvedManifest } from "./manifest";

type Props = { manifest: ResolvedManifest };

const calculateMetadata: CalculateMetadataFunction<Props> = async () => {
  const raw = await fetchManifest(staticFile("captured/manifest.json"));
  const manifest = resolveManifest(raw);

  const clipsTotal = manifest.scenes.reduce(
    (sum, s) => sum + s.durationInFrames,
    0,
  );
  const reportTotal = manifest.reportPages.files.length * REPORT_PAGE_FRAMES;

  return {
    durationInFrames: INTRO_FRAMES + clipsTotal + reportTotal,
    props: { manifest },
  };
};

export const LLExplorerDemo = () => {
  return (
    <Composition
      id="LLExplorerDemo"
      component={DemoVideo}
      durationInFrames={300}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
      calculateMetadata={calculateMetadata}
      defaultProps={{
        manifest: { scenes: [], reportPages: { lang: "de", files: [] } },
      }}
    />
  );
};
