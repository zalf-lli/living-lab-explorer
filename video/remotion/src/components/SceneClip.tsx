import { AbsoluteFill, OffthreadVideo, Sequence, staticFile } from "remotion";
import { CAPTION_TEXT, type SceneConfig } from "../scenes";
import type { ResolvedScene } from "../manifest";
import { Annotation } from "./Annotation";
import { TitleCard } from "./TitleCard";

function humanize(id: string): string {
  return id
    .replace(/^scene-\d+-/, "")
    .split("-")
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(" ");
}

export const SceneClip: React.FC<{
  scene: SceneConfig;
  resolved: ResolvedScene;
}> = ({ scene, resolved }) => {
  if (!resolved.file) {
    return <TitleCard title={humanize(scene.id)} />;
  }

  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <OffthreadVideo
        src={staticFile(`captured/${resolved.file}`)}
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
      />

      {resolved.annotations.map((annotation, i) => {
        const text = CAPTION_TEXT[annotation.key];
        if (!text) return null;
        return (
          <Sequence
            key={`${annotation.key}-${i}`}
            from={annotation.from}
            durationInFrames={annotation.durationInFrames}
          >
            <Annotation annotation={annotation} text={text} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
