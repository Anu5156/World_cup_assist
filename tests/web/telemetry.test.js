/**
 * Unit tests for web/telemetry.js
 *
 * Run with:  npx vitest run
 * Watch:     npx vitest
 *
 * These tests exercise the pure compute layer with no DOM, no server, and no
 * API key. They are designed to catch the class of bug where a telemetry
 * variable (e.g. `tr` for transit status) is accidentally treated as a DOM
 * element rather than a plain string.
 */

import { describe, it, expect } from "vitest";
import {
  badgeClass,
  heatmapClass,
  nodeCongestClass,
  computeQueuePredictions,
  computeTelemetry,
  setElementClass,
} from "../../web/telemetry.js";

// ── Fixture ────────────────────────────────────────────────────────────────────

/** Representative live telemetry payload from the SSE stream. */
const FIXTURE = {
  gate_congestion: { A: "High", B: "Medium", C: "Low", D: "Low" },
  elevator_status:  { A: "Online", B: "Offline", C: "Online", D: "Online" },
  transit_status:   "Minor Delays",
  concession_times: "Busy",
  sensory_room_occupancy: "Near Capacity",
  active_alert: null,
};

// ── badgeClass ─────────────────────────────────────────────────────────────────

describe("badgeClass", () => {
  it("maps 'High' → 'red'",          () => expect(badgeClass("High")).toBe("red"));
  it("maps 'Offline' → 'red'",       () => expect(badgeClass("Offline")).toBe("red"));
  it("maps 'Major Delays' → 'red'",  () => expect(badgeClass("Major Delays")).toBe("red"));
  it("maps 'Full' → 'red'",          () => expect(badgeClass("Full")).toBe("red"));
  it("maps 'Medium' → 'yellow'",     () => expect(badgeClass("Medium")).toBe("yellow"));
  it("maps 'Minor Delays' → 'yellow'", () => expect(badgeClass("Minor Delays")).toBe("yellow"));
  it("maps 'Near Capacity' → 'yellow'", () => expect(badgeClass("Near Capacity")).toBe("yellow"));
  it("maps 'Busy' → 'yellow'",       () => expect(badgeClass("Busy")).toBe("yellow"));
  it("maps 'Low' → 'green'",         () => expect(badgeClass("Low")).toBe("green"));
  it("maps 'On Time' → 'green'",     () => expect(badgeClass("On Time")).toBe("green"));
  it("maps '' (unknown) → 'green'",  () => expect(badgeClass("")).toBe("green"));
});

// ── heatmapClass ───────────────────────────────────────────────────────────────

describe("heatmapClass", () => {
  it("contains 'high' for High level",   () => expect(heatmapClass("High")).toContain("high"));
  it("contains 'med' for Medium level",  () => expect(heatmapClass("Medium")).toContain("med"));
  it("contains 'low' for Low level",     () => expect(heatmapClass("Low")).toContain("low"));
  it("returns a string (not DOM)",       () => expect(typeof heatmapClass("High")).toBe("string"));
});

// ── nodeCongestClass ──────────────────────────────────────────────────────────

describe("nodeCongestClass", () => {
  it("returns 'high-congest' for High",   () => expect(nodeCongestClass("High")).toBe("high-congest"));
  it("returns 'med-congest' for Medium",  () => expect(nodeCongestClass("Medium")).toBe("med-congest"));
  it("returns 'low-congest' for Low",     () => expect(nodeCongestClass("Low")).toBe("low-congest"));
});

describe("setElementClass", () => {
  it("applies classes to HTML elements", () => {
    const el = { className: "" };
    setElementClass(el, "metric-value red");
    expect(el.className).toBe("metric-value red");
  });

  it("applies classes to SVG-like elements via setAttribute", () => {
    const el = { setAttribute: (name, value) => { el[name] = value; } };
    setElementClass(el, "heatmap-glow-circle high");
    expect(el.class).toBe("heatmap-glow-circle high");
  });
});

// ── computeQueuePredictions ───────────────────────────────────────────────────

describe("computeQueuePredictions", () => {
  it("returns all three facilities", () => {
    const q = computeQueuePredictions(FIXTURE);
    expect(q).toHaveProperty("restroom");
    expect(q).toHaveProperty("sensory");
    expect(q).toHaveProperty("concessions");
  });

  it("marks restroom red when all gates are High", () => {
    const s = { gate_congestion: { A: "High", B: "High", C: "High", D: "High" },
                sensory_room_occupancy: "Open" };
    const q = computeQueuePredictions(s);
    expect(q.restroom.cssClass).toBe("red");
    expect(q.restroom.level).toBe("High");
  });

  it("marks sensory red when Full", () => {
    const q = computeQueuePredictions({ ...FIXTURE, sensory_room_occupancy: "Full" });
    expect(q.sensory.cssClass).toBe("red");
  });

  it("marks sensory yellow when Near Capacity", () => {
    const q = computeQueuePredictions(FIXTURE); // FIXTURE has Near Capacity
    expect(q.sensory.cssClass).toBe("yellow");
  });

  it("marks sensory green when Open", () => {
    const q = computeQueuePredictions({ ...FIXTURE, sensory_room_occupancy: "Open" });
    expect(q.sensory.cssClass).toBe("green");
  });

  it("handles missing gate_congestion gracefully", () => {
    const q = computeQueuePredictions({});
    expect(q.restroom.level).toBe("Low");
    expect(q.restroom.cssClass).toBe("green");
  });
});

// ── computeTelemetry ──────────────────────────────────────────────────────────

describe("computeTelemetry", () => {
  it("extracts gA correctly from fixture", () => {
    const t = computeTelemetry(FIXTURE);
    expect(t.gA).toBe("High");
    expect(t.gAClass).toBe("red");
  });

  it("extracts gB correctly from fixture", () => {
    const t = computeTelemetry(FIXTURE);
    expect(t.gB).toBe("Medium");
    expect(t.gBClass).toBe("yellow");
  });

  // ── REGRESSION: const tr bug ──────────────────────────────────────────────
  // Previously `tr` was used both as the transit-status string and accidentally
  // set as a DOM element variable in the same scope, causing
  // `trDot.className = tr` to assign an object instead of a CSS class string,
  // which silently produced `"[object HTMLElement]"` in the DOM.
  //
  // These tests ensure `tr` is always a plain string.

  it("tr is a string, not a DOM element — regression for const tr bug", () => {
    const t = computeTelemetry(FIXTURE);
    expect(typeof t.tr).toBe("string");
    expect(t.tr).toBe("Minor Delays");
  });

  it("trClass is correct for Minor Delays", () => {
    const t = computeTelemetry(FIXTURE);
    expect(t.trClass).toBe("yellow");
  });

  it("trLevel is 'Medium' for Minor Delays", () => {
    const t = computeTelemetry(FIXTURE);
    expect(t.trLevel).toBe("Medium");
  });

  it("trLevel is 'High' for Major Delays", () => {
    const t = computeTelemetry({ ...FIXTURE, transit_status: "Major Delays" });
    expect(t.trLevel).toBe("High");
    expect(t.trClass).toBe("red");
  });

  it("trLevel is 'Low' for On Time", () => {
    const t = computeTelemetry({ ...FIXTURE, transit_status: "On Time" });
    expect(t.trLevel).toBe("Low");
    expect(t.trClass).toBe("green");
  });

  it("defaults all fields when status is empty object", () => {
    const t = computeTelemetry({});
    expect(t.gA).toBe("Low");
    expect(t.gB).toBe("Low");
    expect(t.tr).toBe("On Time");
    expect(t.sr).toBe("Open");
    expect(t.gAClass).toBe("green");
    expect(t.trClass).toBe("green");
    expect(t.trLevel).toBe("Low");
    expect(t.srLevel).toBe("Low");
  });

  it("defaults all fields when status is null/undefined", () => {
    const t = computeTelemetry(null);
    expect(t.tr).toBe("On Time");
    expect(typeof t.tr).toBe("string");
  });

  it("includes queue predictions", () => {
    const t = computeTelemetry(FIXTURE);
    expect(t.queue).toHaveProperty("restroom");
    expect(t.queue).toHaveProperty("sensory");
    expect(t.queue).toHaveProperty("concessions");
  });

  it("srLevel is 'High' when Full", () => {
    const t = computeTelemetry({ ...FIXTURE, sensory_room_occupancy: "Full" });
    expect(t.srLevel).toBe("High");
    expect(t.srClass).toBe("red");
  });

  it("srLevel is 'Medium' when Near Capacity", () => {
    const t = computeTelemetry(FIXTURE);
    expect(t.srLevel).toBe("Medium");
  });

  it("srLevel is 'Low' when Open", () => {
    const t = computeTelemetry({ ...FIXTURE, sensory_room_occupancy: "Open" });
    expect(t.srLevel).toBe("Low");
    expect(t.srClass).toBe("green");
  });
});
