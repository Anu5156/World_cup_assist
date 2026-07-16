/**
 * telemetry.js — Pure telemetry computation helpers.
 *
 * Exported functions are side-effect-free (no DOM access) so they can be
 * unit-tested with vitest + jsdom without a running browser or server.
 *
 * app.js imports these and uses the results to drive DOM updates.
 */

"use strict";

/**
 * Map a telemetry level string to a CSS colour token.
 *
 * @param {string} level  e.g. "High", "Low", "Offline", "Major Delays"
 * @returns {"red"|"yellow"|"green"}
 */
export function badgeClass(level) {
  if (
    level === "High" ||
    level === "Offline" ||
    level === "Major Delays" ||
    level === "Full"
  ) return "red";
  if (
    level === "Medium" ||
    level === "Minor Delays" ||
    level === "Near Capacity" ||
    level === "Busy"
  ) return "yellow";
  return "green";
}

/**
 * Derive a heatmap CSS class string for SVG circle elements.
 *
 * @param {"High"|"Medium"|"Low"} level
 * @returns {string}
 */
export function heatmapClass(level) {
  if (level === "High")   return "heatmap-glow-circle high high-pulse";
  if (level === "Medium") return "heatmap-glow-circle med med-pulse";
  return "heatmap-glow-circle low low-pulse";
}

/**
 * Derive a congestion CSS class for SVG map nodes.
 *
 * @param {"High"|"Medium"|"Low"} level
 * @returns {string}
 */
export function nodeCongestClass(level) {
  if (level === "High")   return "high-congest";
  if (level === "Medium") return "med-congest";
  return "low-congest";
}

/**
 * Compute queue predictions from live gate congestion data.
 *
 * All wait-time formulae live here — never in the browser DOM layer.
 *
 * @param {object} status  Raw StadiumStatus object from the SSE stream.
 * @returns {{
 *   restroom:    {wait: string, pct: number, cssClass: string, level: string},
 *   sensory:     {wait: string, pct: number, cssClass: string},
 *   concessions: {wait: string, pct: number, cssClass: string},
 * }}
 */
export function computeQueuePredictions(status) {
  const gates = ["A", "B", "C", "D"];
  let busyCount = 0;
  gates.forEach(g => {
    const level = status?.gate_congestion?.[g] ?? "Low";
    if (level === "High")   busyCount += 2;
    else if (level === "Medium") busyCount += 1;
  });

  // Restroom load — proportional to gate congestion
  const restLevel = busyCount >= 5 ? "High" : busyCount >= 2 ? "Medium" : "Low";
  const restroom = restLevel === "High"
    ? { wait: "12 mins", pct: 85, cssClass: "red",    level: "High" }
    : restLevel === "Medium"
      ? { wait: "6 mins",  pct: 45, cssClass: "yellow", level: "Medium" }
      : { wait: "2 mins",  pct: 15, cssClass: "green",  level: "Low" };

  // Sensory room — driven by sensory_room_occupancy
  const sr = status?.sensory_room_occupancy ?? "Open";
  const sensory = sr === "Full"
    ? { wait: "Full (20+ min)", pct: 95, cssClass: "red" }
    : sr === "Near Capacity"
      ? { wait: "Near cap (8 min)", pct: 65, cssClass: "yellow" }
      : { wait: "No wait",          pct: 10, cssClass: "green" };

  // Concessions — gate congestion proxy
  const concessions = busyCount >= 6
    ? { wait: "~25 min", pct: 90, cssClass: "red" }
    : busyCount >= 3
      ? { wait: "~15 min", pct: 60, cssClass: "yellow" }
      : { wait: "~5 min",  pct: 20, cssClass: "green" };

  return { restroom, sensory, concessions };
}

/**
 * Derive all computed display values from a raw StadiumStatus object.
 *
 * This is the single source of truth for every derived metric shown in the UI.
 * The function is pure: same input → same output, no side effects.
 *
 * @param {object} status  Raw StadiumStatus (may be partial / empty object).
 * @returns {{
 *   gA: string, gB: string, tr: string, sr: string,
 *   gAClass: string, gBClass: string, trClass: string, srClass: string,
 *   trLevel: "High"|"Medium"|"Low",
 *   srLevel: "High"|"Medium"|"Low",
 *   queue: ReturnType<computeQueuePredictions>,
 * }}
 */
export function setElementClass(el, className) {
  if (!el) return;
  if (typeof el.className === "string") {
    el.className = className;
    return;
  }
  if (typeof el.setAttribute === "function") {
    el.setAttribute("class", className);
  }
}

export function computeTelemetry(status) {
  const s = status ?? {};
  const gA = s.gate_congestion?.A ?? "Low";
  const gB = s.gate_congestion?.B ?? "Low";
  // NOTE: `tr` is the transit STATUS STRING, not a DOM element — this
  // distinction caused the "const tr bug" where callers confused it with a
  // DOM reference and called .className on a string. Regression test: see
  // telemetry.test.js → "tr is a string, not a DOM element".
  const tr = s.transit_status ?? "On Time";
  const sr = s.sensory_room_occupancy ?? "Open";

  const trLevel = tr === "Major Delays" ? "High"
    : tr === "Minor Delays" ? "Medium"
    : "Low";

  const srLevel = sr === "Full" ? "High"
    : sr === "Near Capacity" ? "Medium"
    : "Low";

  return {
    gA, gB, tr, sr,
    gAClass: badgeClass(gA),
    gBClass: badgeClass(gB),
    trClass: badgeClass(tr),
    srClass: badgeClass(sr),
    trLevel,
    srLevel,
    queue: computeQueuePredictions(s),
  };
}
