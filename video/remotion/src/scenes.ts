export const FPS = 30;
export const WIDTH = 1920;
export const HEIGHT = 1080;

// How long each report page is held/panned during the report scene's screenshot scroll.
export const REPORT_PAGE_FRAMES = 105;

export type AnnotationPlace = "below" | "above" | "left" | "right" | "note";

export type Annotation = {
  key: string;
  place: AnnotationPlace;
  rect: { x: number; y: number; width: number; height: number };
  from: number;
  durationInFrames: number;
};

export type SceneConfig = {
  id: string;
  /** Used only when no captured clip exists yet for this scene (see manifest.ts). */
  placeholderSeconds: number;
};

// Order matches the scene plan and video/CONTRACT.md. Switching labs and entering comparison are
// one continuous captured take, so there is no separate compare scene here.
export const SCENES: SceneConfig[] = [
  { id: "scene-01-landing", placeholderSeconds: 5 },
  { id: "scene-02-detail-open", placeholderSeconds: 3 },
  { id: "scene-03-language", placeholderSeconds: 7 },
  { id: "scene-04-tabs-tour", placeholderSeconds: 45 },
  { id: "scene-05-labs-compare", placeholderSeconds: 30 },
  { id: "scene-06-report", placeholderSeconds: 5 },
  { id: "scene-07-partners", placeholderSeconds: 12 },
  { id: "scene-08-contact-manager", placeholderSeconds: 7 },
];

// All on-screen copy lives here, keyed by the annotation keys the capture scripts emit. Keeping
// it out of the capture scripts means wording can change without re-recording any footage.
export const CAPTION_TEXT: Record<string, string> = {
  landingPick: "Fünf Reallabore – eines auswählen",
  language: "Zweisprachig: Deutsch / Englisch",
  tabs: "Thematische Bereiche",
  kpis: "Eigene Kennzahlen je Thema",
  citation: "Datenquellen und Nachweise",
  climatePeriods: "Gegenwart und Klimaprojektionen",
  landPrice: "Bodenrichtwerte – Details beim Überfahren",
  protectedAreas: "Schutzgebiete einblenden",
  switchLabs: "Zwischen Reallaboren wechseln",
  compare: "Zwei Reallabore vergleichen",
  downloadReport: "Bericht als PDF herunterladen",
  partners: "Partner und Projekte",
  partnersWip: "Dieser Bereich wird noch weiter ausgebaut",
  contactManager: "Kontakt zum regionalen Netzwerkmanagement",
};
