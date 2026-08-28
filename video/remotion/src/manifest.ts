import { FPS, SCENES, type Annotation } from "./scenes";

export type ManifestScene = {
  id: string;
  file: string;
  durationInFrames: number;
  annotations?: Annotation[];
};

export type ReportPages = {
  lang: string;
  count: number;
  /** Ordered page image filenames; falls back to page-1..page-N when absent. */
  files?: string[];
};

export type Manifest = {
  fps: number;
  scenes: ManifestScene[];
  reportPages: ReportPages;
};

export type ResolvedScene = {
  id: string;
  /** Path relative to public/captured/, or null if not captured yet. */
  file: string | null;
  durationInFrames: number;
  annotations: Annotation[];
};

export type ResolvedManifest = {
  scenes: ResolvedScene[];
  reportPages: { lang: string; files: string[] };
};

/**
 * Merges the real manifest.json (if present) with the SCENES config, so a partially-captured
 * video still renders self-consistently: scenes already captured play as real footage, the rest
 * fall back to a placeholder card sized from `placeholderSeconds`.
 */
export function resolveManifest(raw: Manifest | null): ResolvedManifest {
  const byId = new Map((raw?.scenes ?? []).map((s) => [s.id, s]));
  const scenes: ResolvedScene[] = SCENES.map((cfg) => {
    const found = byId.get(cfg.id);
    if (found) {
      return {
        id: cfg.id,
        file: found.file,
        durationInFrames: found.durationInFrames,
        annotations: found.annotations ?? [],
      };
    }
    return {
      id: cfg.id,
      file: null,
      durationInFrames: FPS * cfg.placeholderSeconds,
      annotations: [],
    };
  });

  const rp = raw?.reportPages;
  const files =
    rp?.files ??
    Array.from({ length: rp?.count ?? 0 }, (_, i) => `page-${i + 1}.png`);

  return {
    scenes,
    reportPages: { lang: rp?.lang ?? "de", files },
  };
}

export async function fetchManifest(url: string): Promise<Manifest | null> {
  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    return (await res.json()) as Manifest;
  } catch {
    return null;
  }
}
