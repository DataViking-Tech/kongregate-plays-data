import fs from "node:fs/promises";
import path from "node:path";

const root = path.resolve(".");
const rankedJsonPath = path.join(root, "data", "processed", "ranked_games.json");
const metricsJsonPath = path.join(root, "data", "processed", "game_play_history.json");
const outputDir = path.join(root, "outputs", "kongregate_ranked_games");
const htmlPath = path.join(outputDir, "play_count_bar_chart_race.html");
const dataPath = path.join(outputDir, "play_count_bar_chart_race_data.json");
const sheetUrl = "https://docs.google.com/spreadsheets/d/1LCClWPFrrxuiJeu9C15ZJfkFEaf6GONO6ChHalAxtx4";

const topN = 12;

async function readJsonRows(filePath) {
  try {
    const payload = JSON.parse(await fs.readFile(filePath, "utf8"));
    return payload.rows ?? [];
  } catch (error) {
    if (error.code === "ENOENT") return [];
    throw error;
  }
}

function gameUrlParts(gameUrl) {
  if (!gameUrl) return null;
  try {
    const parsed = new URL(gameUrl);
    const match = parsed.pathname.match(/^\/(?:en\/)?games\/([^/]+)\/([^/]+)/);
    if (!match) return null;
    return {
      developer: decodeURIComponent(match[1]),
      slug: decodeURIComponent(match[2]),
    };
  } catch {
    return null;
  }
}

function canonicalGameUrl(gameUrl) {
  const parts = gameUrlParts(gameUrl);
  if (!parts) return gameUrl || "";
  return `www.kongregate.com/games/${parts.developer}/${parts.slug}`.toLowerCase();
}

function developerFromUrl(gameUrl) {
  return gameUrlParts(gameUrl)?.developer ?? "";
}

function gameKey(row) {
  if (row.game_url) return canonicalGameUrl(row.game_url);
  return `${row.game_name ?? ""}|${row.developer ?? ""}`.toLowerCase();
}

function chartGameKey(row) {
  const parts = gameUrlParts(row.game_url);
  if (parts?.slug) return `kongregate-game:${parts.slug.toLowerCase()}`;
  return gameKey(row);
}

function compactSource(row) {
  if (row.parser === "metrics_json") return "metrics_json";
  if (row.parser === "live_metrics_json") return "live_metrics_json";
  const parts = [];
  if (row.ranking_type) parts.push(row.ranking_type);
  if (row.category) parts.push(row.category);
  return parts.join(" / ");
}

function normalizeObservedRow(row) {
  const plays = Number(row.plays_count_observed);
  if (!Number.isFinite(plays) || plays <= 0) return null;
  return {
    ...row,
    plays_count_observed: plays,
    rank_on_date: row.rank_on_date ?? "",
    developer: row.developer || developerFromUrl(row.game_url) || "",
    parser: row.parser || "",
  };
}

function buildFrames(rows, sourceCounts) {
  const observedRows = rows
    .map(normalizeObservedRow)
    .filter(Boolean)
    .sort((a, b) => {
      const byDate = String(a.date).localeCompare(String(b.date));
      if (byDate !== 0) return byDate;
      return Number(a.rank_on_date ?? 999999) - Number(b.rank_on_date ?? 999999);
    });

  const rowsByDate = new Map();
  for (const row of observedRows) {
    if (!rowsByDate.has(row.date)) rowsByDate.set(row.date, []);
    rowsByDate.get(row.date).push(row);
  }

  const dates = [...rowsByDate.keys()].sort();
  const bestByGame = new Map();
  const frames = [];

  for (const date of dates) {
    const rowsForDate = rowsByDate.get(date);

    for (const row of rowsForDate) {
      const key = chartGameKey(row);
      const plays = Number(row.plays_count_observed);
      const previous = bestByGame.get(key);
      if (!previous || plays >= previous.plays) {
        bestByGame.set(key, {
          key,
          gameName: row.game_name,
          developer: row.developer || "",
          gameUrl: row.game_url || "",
          plays,
          lastObservedDate: row.date,
          rankOnDate: row.rank_on_date ?? "",
          source: compactSource(row),
        });
      }
    }

    const entries = [...bestByGame.values()]
      .sort((a, b) => b.plays - a.plays || a.gameName.localeCompare(b.gameName))
      .slice(0, topN)
      .map((entry, index) => ({
        ...entry,
        rank: index + 1,
      }));

    frames.push({
      date,
      observedRows: rowsForDate.length,
      trackedGames: bestByGame.size,
      entries,
    });
  }

  return {
    generatedAt: new Date().toISOString(),
    sheetUrl,
    summary: {
      observedRows: observedRows.length,
      ...sourceCounts,
      frameCount: frames.length,
      firstDate: dates[0] ?? null,
      lastDate: dates.at(-1) ?? null,
      topN,
      method: "Ranks each game by the highest play count observed up to each archived ranked-list or metrics capture date; developer-renamed URLs are merged by game slug for chart continuity.",
    },
    frames,
  };
}

function htmlDocument() {
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="data:,">
  <title>Kongregate Observed Plays Race</title>
  <style>
    :root {
      color-scheme: light;
      --page: #f7f5ef;
      --ink: #202326;
      --muted: #687076;
      --line: #d8d3c8;
      --panel: #fffdf8;
      --accent: #2364aa;
      --track: #ebe6dc;
      --shadow: 0 18px 45px rgba(33, 35, 38, 0.12);
      --move-duration: 760ms;
      --move-ease: cubic-bezier(0.18, 0.78, 0.2, 1);
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      background: var(--page);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }

    main {
      width: min(1180px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 28px 0 34px;
    }

    header {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 18px;
      align-items: end;
      border-bottom: 1px solid var(--line);
      padding-bottom: 18px;
    }

    h1 {
      margin: 0;
      font-size: clamp(24px, 3.4vw, 46px);
      line-height: 1.02;
      font-weight: 760;
    }

    .subtitle {
      margin: 8px 0 0;
      color: var(--muted);
      font-size: 15px;
      line-height: 1.45;
      max-width: 760px;
    }

    .dateBlock {
      text-align: right;
      min-width: 210px;
    }

    .dateLabel {
      font-size: clamp(32px, 5vw, 64px);
      line-height: 0.92;
      font-weight: 800;
      font-variant-numeric: tabular-nums;
    }

    .dateMeta {
      margin-top: 8px;
      color: var(--muted);
      font-size: 13px;
      font-variant-numeric: tabular-nums;
    }

    .toolbar {
      display: grid;
      grid-template-columns: auto minmax(180px, 1fr) auto auto auto;
      gap: 12px;
      align-items: center;
      padding: 16px 0 18px;
    }

    button {
      width: 42px;
      height: 42px;
      border: 1px solid #bfc3c7;
      background: #ffffff;
      color: var(--ink);
      display: inline-grid;
      place-items: center;
      cursor: pointer;
      border-radius: 8px;
      box-shadow: 0 5px 16px rgba(33, 35, 38, 0.08);
    }

    button:hover {
      border-color: #8e969d;
      background: #f8fafb;
    }

    button svg {
      width: 20px;
      height: 20px;
      fill: currentColor;
    }

    .segmented {
      display: inline-grid;
      grid-template-columns: 1fr 1fr;
      border: 1px solid #bfc3c7;
      background: #ffffff;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 5px 16px rgba(33, 35, 38, 0.08);
    }

    .modeButton {
      width: auto;
      min-width: 82px;
      height: 40px;
      border: 0;
      border-radius: 0;
      box-shadow: none;
      color: var(--muted);
      font-size: 13px;
      font-weight: 720;
      background: #ffffff;
    }

    .modeButton + .modeButton {
      border-left: 1px solid #d8dce0;
    }

    .modeButton.isActive {
      background: var(--accent);
      color: #ffffff;
    }

    input[type="range"] {
      width: 100%;
      accent-color: var(--accent);
    }

    .speed {
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--muted);
      font-size: 13px;
      white-space: nowrap;
    }

    .links {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 12px;
    }

    .sheetLink {
      color: var(--accent);
      font-size: 13px;
      text-decoration: none;
      white-space: nowrap;
    }

    .sheetLink:hover {
      text-decoration: underline;
    }

    .chart {
      position: relative;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      padding: clamp(14px, 2.2vw, 24px);
      min-height: 690px;
      overflow: hidden;
    }

    .axis {
      height: 24px;
      display: grid;
      grid-template-columns: 56px 240px minmax(220px, 1fr) 108px;
      gap: 14px;
      color: var(--muted);
      font-size: 12px;
      align-items: center;
      border-bottom: 1px solid var(--line);
      margin-bottom: 8px;
    }

    .axis span {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .rows {
      position: relative;
      height: 640px;
    }

    .barRow {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 46px;
      display: grid;
      grid-template-columns: 56px 240px minmax(220px, 1fr) 108px;
      gap: 14px;
      align-items: center;
      opacity: 0;
      transform: translate3d(0, 0, 0);
      z-index: 1;
      transition:
        transform var(--move-duration) var(--move-ease),
        opacity 240ms ease;
      will-change: transform;
      backface-visibility: hidden;
      contain: layout paint;
    }

    .barRow.isVisible {
      opacity: 1;
      z-index: 2;
    }

    .barRow.isExiting {
      opacity: 0;
      pointer-events: none;
      z-index: 0;
    }

    .rank {
      color: var(--muted);
      font-size: 18px;
      font-weight: 760;
      text-align: right;
      font-variant-numeric: tabular-nums;
    }

    .name {
      min-width: 0;
    }

    .gameName {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-size: 15px;
      font-weight: 740;
    }

    a.gameName {
      color: var(--ink);
      text-decoration: none;
    }

    a.gameName:hover {
      color: var(--accent);
      text-decoration: underline;
    }

    .developer {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      color: var(--muted);
      font-size: 12px;
      margin-top: 2px;
    }

    .track {
      position: relative;
      height: 28px;
      background: var(--track);
      overflow: hidden;
      border-radius: 6px;
    }

    .bar {
      position: absolute;
      inset: 0 auto 0 0;
      width: 100%;
      border-radius: 6px;
      transform: scaleX(0.015);
      transform-origin: left center;
      transition: transform var(--move-duration) var(--move-ease);
    }

    .value {
      text-align: right;
      font-size: 14px;
      font-weight: 760;
      font-variant-numeric: tabular-nums;
      white-space: nowrap;
    }

    .footerMeta {
      display: flex;
      justify-content: space-between;
      gap: 14px;
      align-items: center;
      margin-top: 14px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.4;
    }

    .empty {
      padding: 80px 24px;
      text-align: center;
      color: var(--muted);
    }

    @media (max-width: 780px) {
      main {
        width: min(100vw - 20px, 1180px);
        padding-top: 18px;
      }

      header {
        grid-template-columns: 1fr;
      }

      .dateBlock {
        text-align: left;
      }

      .toolbar {
        grid-template-columns: auto minmax(120px, 1fr);
      }

      .segmented,
      .speed,
      .links {
        grid-column: span 2;
      }

      .links {
        justify-content: flex-start;
      }

      .chart {
        min-height: 690px;
        padding: 12px;
      }

      .axis,
      .barRow {
        grid-template-columns: 30px minmax(84px, 116px) minmax(76px, 1fr) 58px;
        gap: 6px;
      }

      .gameName {
        font-size: 12px;
      }

      .developer {
        display: none;
      }

      .value {
        font-size: 11px;
      }

      .barRow {
        transition:
          transform var(--move-duration) var(--move-ease),
          opacity 180ms ease;
      }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <section>
        <h1>Kongregate observed plays race</h1>
        <p class="subtitle">Top games ranked by highest play count observed up to each archived capture date.</p>
      </section>
      <section class="dateBlock" aria-live="polite">
        <div class="dateLabel" id="dateLabel">0000-00-00</div>
        <div class="dateMeta" id="dateMeta">0 games tracked</div>
      </section>
    </header>

    <section class="toolbar" aria-label="Animation controls">
      <button id="playToggle" title="Play or pause" aria-label="Play or pause">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path id="playIcon" d="M8 5v14l11-7z"></path></svg>
      </button>
      <input id="frameSlider" type="range" min="0" value="0" step="1" aria-label="Date">
      <div class="segmented" role="group" aria-label="Playback cadence">
        <button class="modeButton isActive" type="button" data-mode="smooth" aria-pressed="true">Smooth</button>
        <button class="modeButton" type="button" data-mode="captures" aria-pressed="false">Captures</button>
      </div>
        <label class="speed">Speed <input id="speedSlider" type="range" min="850" max="3200" value="1050" step="50" aria-label="Speed"></label>
      <nav class="links" aria-label="Data links">
        <a class="sheetLink" href="${sheetUrl}" target="_blank" rel="noreferrer">Google Sheet</a>
        <a class="sheetLink" id="dataLink" href="outputs/kongregate_ranked_games/play_count_bar_chart_race_data.json" target="_blank" rel="noreferrer">Data JSON</a>
      </nav>
    </section>

    <section class="chart" aria-label="Animated ranking chart">
      <div class="axis">
        <span>Rank</span>
        <span>Game</span>
        <span>Observed plays</span>
        <span>Count</span>
      </div>
      <div class="rows" id="rows"><div class="empty">Loading chart data...</div></div>
      <div class="footerMeta">
        <span id="sourceMeta"></span>
        <span id="rangeMeta"></span>
      </div>
    </section>
  </main>

  <script>
    let PAYLOAD = null;
    let rawFrames = [];
    let frames = [];
    const palette = ["#2364aa", "#3da35d", "#f29e4c", "#c44536", "#5b6c5d", "#7b5ea7", "#2ca6a4", "#d8578a", "#8a6f3d", "#487d74", "#b85042", "#4b6fad"];
    const rowsEl = document.getElementById("rows");
    const dateLabel = document.getElementById("dateLabel");
    const dateMeta = document.getElementById("dateMeta");
    const sourceMeta = document.getElementById("sourceMeta");
    const rangeMeta = document.getElementById("rangeMeta");
    const frameSlider = document.getElementById("frameSlider");
    const speedSlider = document.getElementById("speedSlider");
    const playToggle = document.getElementById("playToggle");
    const dataLink = document.getElementById("dataLink");
    const modeButtons = [...document.querySelectorAll(".modeButton")];
    const playIcon = document.getElementById("playIcon");
    const playPath = "M8 5v14l11-7z";
    const pausePath = "M7 5h4v14H7zm6 0h4v14h-4z";
    const rowStep = 54;
    const visibleRows = 12;
    const transitionMs = 760;
    const exitMs = transitionMs + 100;
    const smoothStepsPerMonth = 8;
    const rowsByKey = new Map();

    let frameIndex = 0;
    let isPlaying = true;
    let timer = null;
    let playbackMode = "smooth";

    async function loadPayload() {
      const candidates = [
        "outputs/kongregate_ranked_games/play_count_bar_chart_race_data.json",
        "play_count_bar_chart_race_data.json",
      ];
      let lastError = null;
      for (const candidate of candidates) {
        try {
          const separator = candidate.includes("?") ? "&" : "?";
          const dataUrl = \`\${candidate}\${separator}v=\${Date.now()}\`;
          const response = await fetch(dataUrl, { cache: "no-store" });
          if (response.ok) {
            document.documentElement.dataset.chartDataSource = response.url;
            return response.json();
          }
          lastError = new Error(\`\${candidate} returned \${response.status}\`);
        } catch (error) {
          lastError = error;
        }
      }
      throw lastError || new Error("Chart data could not be loaded.");
    }

    function monthIdFromDate(dateText) {
      return String(dateText || "").slice(0, 7);
    }

    function addMonths(monthId, count) {
      const [year, month] = monthId.split("-").map(Number);
      const date = new Date(Date.UTC(year, month - 1 + count, 1));
      return \`\${date.getUTCFullYear()}-\${String(date.getUTCMonth() + 1).padStart(2, "0")}\`;
    }

    function compareFrameDate(frame, targetDate) {
      return String(frame.sourceDate || frame.date).localeCompare(String(targetDate));
    }

    function buildMonthlyKeyframes(sourceFrames) {
      if (!sourceFrames.length) return [];

      const byMonth = new Map();
      for (const frame of sourceFrames) {
        byMonth.set(monthIdFromDate(frame.date), frame);
      }

      const firstMonth = monthIdFromDate(sourceFrames[0].date);
      const lastMonth = monthIdFromDate(sourceFrames.at(-1).date);
      const monthlyFrames = [];
      let latestFrame = sourceFrames[0];
      let cursor = firstMonth;

      while (cursor <= lastMonth) {
        latestFrame = byMonth.get(cursor) || latestFrame;
        monthlyFrames.push({
          ...latestFrame,
          date: cursor,
          displayDate: cursor,
          sourceDate: latestFrame.date,
          cadence: "monthly",
        });
        cursor = addMonths(cursor, 1);
      }

      return monthlyFrames;
    }

    function frameEntryMap(frame) {
      return new Map((frame.entries || []).map((entry) => [entry.key, entry]));
    }

    function smoothRatio(ratio) {
      return ratio * ratio * (3 - (2 * ratio));
    }

    function numericMonth(monthId) {
      const [year, month] = String(monthId).split("-").map(Number);
      return (year * 12) + month - 1;
    }

    function monthFromNumeric(value) {
      const year = Math.floor(value / 12);
      const month = (value % 12) + 1;
      return \`\${year}-\${String(month).padStart(2, "0")}\`;
    }

    function interpolatedMonth(startMonth, endMonth, ratio) {
      const start = numericMonth(startMonth);
      const end = numericMonth(endMonth);
      return monthFromNumeric(Math.round(start + ((end - start) * ratio)));
    }

    function parseChartDate(dateText) {
      const value = String(dateText || "");
      const normalized = value.length === 7 ? \`\${value}-01\` : value;
      const date = new Date(\`\${normalized}T00:00:00Z\`);
      return Number.isNaN(date.getTime()) ? null : date;
    }

    function formatChartDate(date) {
      return [
        date.getUTCFullYear(),
        String(date.getUTCMonth() + 1).padStart(2, "0"),
        String(date.getUTCDate()).padStart(2, "0"),
      ].join("-");
    }

    function interpolatedDate(startFrame, endFrame, ratio) {
      const startDate = parseChartDate(startFrame.sourceDate || startFrame.date);
      const endDate = parseChartDate(endFrame.sourceDate || endFrame.date);
      if (!startDate || !endDate) {
        const startMonth = monthIdFromDate(startFrame.displayDate || startFrame.date);
        const endMonth = monthIdFromDate(endFrame.displayDate || endFrame.date);
        return interpolatedMonth(startMonth, endMonth, ratio);
      }
      const start = startDate.getTime();
      const end = endDate.getTime();
      return formatChartDate(new Date(start + ((end - start) * ratio)));
    }

    function interpolatedNumber(start, end, ratio) {
      const fromValue = Number(start) || 0;
      const toValue = Number(end) || fromValue;
      return Math.round(fromValue + ((toValue - fromValue) * ratio));
    }

    function interpolateFrame(startFrame, endFrame, ratio) {
      const eased = smoothRatio(ratio);
      const startEntries = frameEntryMap(startFrame);
      const endEntries = frameEntryMap(endFrame);
      const keys = new Set([...startEntries.keys(), ...endEntries.keys()]);
      const startFloor = Math.max(1, Math.min(...(startFrame.entries || []).map((entry) => entry.plays)));
      const endFloor = Math.max(1, Math.min(...(endFrame.entries || []).map((entry) => entry.plays)));
      const joinFloor = Math.max(1, Math.min(startFloor, endFloor));
      const entries = [...keys]
        .map((key) => {
          const startEntry = startEntries.get(key);
          const endEntry = endEntries.get(key);
          const baseEntry = endEntry || startEntry;
          const startPlays = startEntry ? startEntry.plays : Math.min(endEntry.plays, joinFloor);
          const endPlays = endEntry ? endEntry.plays : startEntry.plays;
          const targetRank = endEntry?.rank ?? (visibleRows + (startEntry?.rank ?? visibleRows));
          return {
            ...baseEntry,
            plays: interpolatedNumber(startPlays, endPlays, eased),
            _sortRank: targetRank,
          };
        })
        .sort((a, b) => a._sortRank - b._sortRank || b.plays - a.plays || a.gameName.localeCompare(b.gameName))
        .slice(0, visibleRows)
        .map(({ _sortRank, ...entry }, index) => ({
          ...entry,
          rank: index + 1,
        }));

      const displayDate = interpolatedDate(startFrame, endFrame, ratio);

      return {
        ...endFrame,
        date: displayDate,
        displayDate,
        sourceDate: startFrame.sourceDate || startFrame.date,
        fromSourceDate: startFrame.sourceDate || startFrame.date,
        toSourceDate: endFrame.sourceDate || endFrame.date,
        interpolated: true,
        observedRows: interpolatedNumber(startFrame.observedRows, endFrame.observedRows, eased),
        trackedGames: interpolatedNumber(startFrame.trackedGames, endFrame.trackedGames, eased),
        scaleMax: interpolatedNumber(frameScaleMax(startFrame.entries || []), frameScaleMax(endFrame.entries || []), eased),
        entries,
      };
    }

    function buildSmoothFrames(sourceFrames) {
      const keyframes = buildMonthlyKeyframes(sourceFrames);
      if (keyframes.length <= 1) return keyframes;

      const smoothFrames = [keyframes[0]];
      for (let index = 1; index < keyframes.length; index += 1) {
        const startFrame = keyframes[index - 1];
        const endFrame = keyframes[index];
        for (let step = 1; step < smoothStepsPerMonth; step += 1) {
          smoothFrames.push(interpolateFrame(startFrame, endFrame, step / smoothStepsPerMonth));
        }
        smoothFrames.push(endFrame);
      }

      return smoothFrames;
    }

    function frameScaleMax(entries) {
      const topValue = Math.max(1, ...entries.map((entry) => entry.plays || 0));
      return topValue * 1.08;
    }

    function updateModeButtons() {
      for (const button of modeButtons) {
        const active = button.dataset.mode === playbackMode;
        button.classList.toggle("isActive", active);
        button.setAttribute("aria-pressed", String(active));
      }
    }

    function updateRangeMeta() {
      if (!frames.length) {
        rangeMeta.textContent = "No observed play counts found";
        return;
      }
      const cadence = playbackMode === "smooth" ? "smooth frames" : "capture frames";
      rangeMeta.textContent = \`\${PAYLOAD.summary.firstDate} to \${PAYLOAD.summary.lastDate} | \${PAYLOAD.summary.observedRows.toLocaleString()} observed rows | \${frames.length.toLocaleString()} \${cadence}\`;
    }

    function closestFrameIndex(targetDate) {
      if (!frames.length || !targetDate) return 0;
      const found = frames.findIndex((frame) => compareFrameDate(frame, targetDate) >= 0);
      return found === -1 ? frames.length - 1 : found;
    }

    function setPlaybackMode(mode, targetDate) {
      playbackMode = mode;
      frames = playbackMode === "smooth" ? buildSmoothFrames(rawFrames) : rawFrames;
      frameIndex = closestFrameIndex(targetDate);
      frameSlider.max = Math.max(frames.length - 1, 0);
      frameSlider.value = String(frameIndex);
      updateModeButtons();
      updateRangeMeta();
    }

    function formatPlays(value) {
      if (value >= 1_000_000_000) return \`\${(value / 1_000_000_000).toFixed(1)}B\`;
      if (value >= 1_000_000) return \`\${(value / 1_000_000).toFixed(value >= 10_000_000 ? 0 : 1)}M\`;
      if (value >= 1_000) return \`\${(value / 1_000).toFixed(value >= 100_000 ? 0 : 1)}K\`;
      return value.toLocaleString();
    }

    function colorFor(key) {
      let hash = 0;
      for (let i = 0; i < key.length; i += 1) hash = ((hash << 5) - hash + key.charCodeAt(i)) | 0;
      return palette[Math.abs(hash) % palette.length];
    }

    function detailText(entry) {
      const parts = [];
      if (entry.developer) parts.push(entry.developer);
      if (entry.lastObservedDate) parts.push(\`seen \${entry.lastObservedDate}\`);
      if (!parts.length && entry.source) parts.push(entry.source);
      return parts.join(" | ") || "Kongregate";
    }

    function rowElement(entry) {
      const row = document.createElement("div");
      row.className = "barRow";
      row.dataset.key = entry.key;
      row.style.transform = \`translate3d(0, \${rowStep * visibleRows}px, 0)\`;

      const rank = document.createElement("div");
      rank.className = "rank";
      rank.textContent = entry.rank;

      const name = document.createElement("div");
      name.className = "name";
      const gameName = document.createElement(entry.gameUrl ? "a" : "div");
      gameName.className = "gameName";
      gameName.textContent = entry.gameName;
      if (entry.gameUrl) {
        gameName.href = entry.gameUrl;
        gameName.target = "_blank";
        gameName.rel = "noreferrer";
      }
      const developer = document.createElement("div");
      developer.className = "developer";
      developer.textContent = detailText(entry);
      name.append(gameName, developer);

      const track = document.createElement("div");
      track.className = "track";
      const bar = document.createElement("div");
      bar.className = "bar";
      bar.style.background = colorFor(entry.key);
      track.append(bar);

      const value = document.createElement("div");
      value.className = "value";

      row.append(rank, name, track, value);
      return row;
    }

    function animateValue(valueEl, nextValue) {
      const previousValue = Number(valueEl.dataset.rawValue || nextValue);
      const targetValue = Number(nextValue);
      valueEl.dataset.rawValue = String(targetValue);

      if (!Number.isFinite(previousValue) || previousValue === targetValue) {
        valueEl.textContent = formatPlays(targetValue);
        return;
      }

      const startedAt = performance.now();
      const animationToken = String(startedAt);
      valueEl.dataset.animationToken = animationToken;

      function tick(now) {
        if (valueEl.dataset.animationToken !== animationToken) return;
        const progress = Math.min((now - startedAt) / transitionMs, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const displayValue = Math.round(previousValue + ((targetValue - previousValue) * eased));
        valueEl.textContent = formatPlays(displayValue);
        if (progress < 1) requestAnimationFrame(tick);
      }

      requestAnimationFrame(tick);
    }

    function updateRow(row, entry, maxValue) {
      row.querySelector(".rank").textContent = entry.rank;
      const gameName = row.querySelector(".gameName");
      gameName.textContent = entry.gameName;
      if (entry.gameUrl && gameName.tagName === "A") gameName.href = entry.gameUrl;
      row.querySelector(".developer").textContent = detailText(entry);
      animateValue(row.querySelector(".value"), entry.plays);
      row.querySelector(".bar").style.transform = \`scaleX(\${Math.max(0.015, entry.plays / maxValue)})\`;
    }

    function removeInactiveRow(key, row) {
      if (row.dataset.exiting === "true") return;
      row.dataset.exiting = "true";
      row.classList.remove("isVisible");
      row.classList.add("isExiting");
      row.style.transform = \`translate3d(0, \${rowStep * visibleRows}px, 0)\`;

      clearTimeout(row._removeTimer);
      row._removeTimer = setTimeout(() => {
        if (row.dataset.exiting !== "true") return;
        rowsByKey.delete(key);
        row.remove();
      }, exitMs);
    }

    function renderFrame(nextIndex) {
      if (!frames.length) {
        rowsEl.innerHTML = '<div class="empty">No observed play counts found.</div>';
        return;
      }

      const frame = frames[nextIndex];
      const entries = frame.entries.slice(0, visibleRows);
      const maxValue = Number.isFinite(frame.scaleMax) ? frame.scaleMax : frameScaleMax(entries);
      const activeKeys = new Set();

      dateLabel.textContent = frame.displayDate || frame.date;
      dateMeta.textContent = \`\${frame.trackedGames.toLocaleString()} games tracked\`;
      sourceMeta.textContent = frame.interpolated
        ? frame.fromSourceDate === frame.toSourceDate
          ? \`holding latest capture \${frame.fromSourceDate} | \${frame.observedRows.toLocaleString()} observed rows\`
          : \`between \${frame.fromSourceDate} and \${frame.toSourceDate} | \${frame.observedRows.toLocaleString()} observed rows\`
        : frame.sourceDate && frame.sourceDate !== frame.date
        ? \`source capture \${frame.sourceDate} | \${frame.observedRows.toLocaleString()} observed rows\`
        : \`\${frame.observedRows.toLocaleString()} observed rows on this date\`;
      frameSlider.value = String(nextIndex);

      if (rowsEl.dataset.ready !== "true") {
        rowsEl.replaceChildren();
        rowsEl.dataset.ready = "true";
      }

      entries.forEach((entry, index) => {
        let row = rowsByKey.get(entry.key);
        const isNew = !row;
        if (!row) {
          row = rowElement(entry);
          rowsByKey.set(entry.key, row);
          row.style.transition = "none";
          row.style.transform = \`translate3d(0, \${rowStep * visibleRows}px, 0)\`;
          rowsEl.append(row);
          row.getBoundingClientRect();
          row.style.transition = "";
        }
        updateRow(row, entry, maxValue);
        row.dataset.exiting = "false";
        clearTimeout(row._removeTimer);
        row.classList.remove("isExiting");
        const targetTransform = \`translate3d(0, \${index * rowStep}px, 0)\`;
        activeKeys.add(entry.key);
        if (isNew) {
          requestAnimationFrame(() => {
            row.style.transform = targetTransform;
            row.classList.add("isVisible");
          });
        } else {
          row.style.transform = targetTransform;
          row.classList.add("isVisible");
        }
      });

      for (const [key, row] of rowsByKey) {
        if (activeKeys.has(key)) continue;
        removeInactiveRow(key, row);
      }
    }

    async function init() {
      try {
        PAYLOAD = await loadPayload();
        rawFrames = PAYLOAD.frames || [];
        if (dataLink && document.documentElement.dataset.chartDataSource) {
          dataLink.href = document.documentElement.dataset.chartDataSource;
        }
        setPlaybackMode(playbackMode);
        playIcon.setAttribute("d", pausePath);
        renderFrame(frameIndex);
        schedule();
      } catch (error) {
        console.error(error);
        isPlaying = false;
        playIcon.setAttribute("d", playPath);
        rowsEl.innerHTML = '<div class="empty">Chart data could not be loaded.</div>';
        rangeMeta.textContent = "Chart data unavailable";
        dateLabel.textContent = "---- -- --";
        dateMeta.textContent = "";
      }
    }

    function schedule() {
      clearTimeout(timer);
      if (!isPlaying || frames.length <= 1) return;
      const delay = Math.max(Number(speedSlider.value), transitionMs + 100);
      timer = setTimeout(() => {
        frameIndex = (frameIndex + 1) % frames.length;
        renderFrame(frameIndex);
        schedule();
      }, delay);
    }

    playToggle.addEventListener("click", () => {
      isPlaying = !isPlaying;
      playIcon.setAttribute("d", isPlaying ? pausePath : playPath);
      schedule();
    });

    frameSlider.addEventListener("input", (event) => {
      if (!frames.length) return;
      frameIndex = Number(event.target.value);
      renderFrame(frameIndex);
      schedule();
    });

    for (const button of modeButtons) {
      button.addEventListener("click", () => {
        if (button.dataset.mode === playbackMode) return;
        const targetDate = frames[frameIndex]?.sourceDate || frames[frameIndex]?.date;
        setPlaybackMode(button.dataset.mode, targetDate);
        renderFrame(frameIndex);
        schedule();
      });
    }

    speedSlider.addEventListener("input", schedule);

    init();
  </script>
</body>
</html>
`;
}

async function main() {
  const rankedRows = await readJsonRows(rankedJsonPath);
  const metricsRows = await readJsonRows(metricsJsonPath);
  const framesPayload = buildFrames([...rankedRows, ...metricsRows], {
    rankedObservedRows: rankedRows.filter((row) => Number(row.plays_count_observed) > 0).length,
    metricsObservedRows: metricsRows.filter((row) => Number(row.plays_count_observed) > 0).length,
  });
  await fs.mkdir(outputDir, { recursive: true });
  await fs.writeFile(dataPath, `${JSON.stringify(framesPayload, null, 2)}\n`);
  await fs.writeFile(htmlPath, htmlDocument());
  console.log(JSON.stringify({
    htmlPath,
    dataPath,
    ...framesPayload.summary,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
