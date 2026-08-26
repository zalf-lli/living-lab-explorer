import { Fragment } from "react";
import { AbsoluteFill, Series } from "remotion";
import { REPORT_PAGE_FRAMES, SCENES } from "./scenes";
import type { ResolvedManifest } from "./manifest";
import { SceneClip } from "./components/SceneClip";
import { ReportScroll } from "./components/ReportScroll";

// The PDF page-scroll is spliced in immediately after the download click.
const REPORT_SCENE_ID = "scene-06-report";

export const DemoVideo: React.FC<{ manifest: ResolvedManifest }> = ({
  manifest,
}) => {
  const byId = new Map(manifest.scenes.map((s) => [s.id, s]));
  const reportFiles = manifest.reportPages.files;

  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {/* Straight cuts between scenes. Each captured clip already has its loading lead-in
          trimmed off (see video/capture/src/lib/sceneRunner.mjs), so a cut lands on settled UI
          and needs no transition to cover a flash. */}
      <Series>
        {SCENES.map((scene) => {
          const resolved = byId.get(scene.id);
          if (!resolved) return null;

          return (
            <Fragment key={scene.id}>
              <Series.Sequence durationInFrames={resolved.durationInFrames}>
                <SceneClip scene={scene} resolved={resolved} />
              </Series.Sequence>
              {scene.id === REPORT_SCENE_ID && reportFiles.length > 0 ? (
                <Series.Sequence
                  durationInFrames={reportFiles.length * REPORT_PAGE_FRAMES}
                >
                  <ReportScroll
                    lang={manifest.reportPages.lang}
                    files={reportFiles}
                  />
                </Series.Sequence>
              ) : null}
            </Fragment>
          );
        })}
      </Series>
    </AbsoluteFill>
  );
};
