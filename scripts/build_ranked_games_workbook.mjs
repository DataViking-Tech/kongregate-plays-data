import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = path.resolve(".");
const rankedJsonPath = path.join(root, "data", "processed", "ranked_games.json");
const miniCatalogJsonPath = path.join(root, "data", "processed", "mini_catalog.json");
const gamePlayHistoryJsonPath = path.join(root, "data", "processed", "game_play_history.json");
const reportJsonPath = path.join(root, "logs", "ranked_games_report.json");
const outputDir = path.join(root, "outputs", "kongregate_ranked_games");
const previewDir = path.join(outputDir, "previews");

const rankedColumns = [
  "date",
  "game_name",
  "rank_on_date",
  "ranking_type",
  "ranking_basis",
  "plays_count_observed",
  "plays_rank_within_capture",
  "plays_rank_scope",
  "category",
  "source_url",
  "capture_timestamp",
  "capture_url",
  "game_url",
  "developer",
  "rating_text",
  "plays_text",
  "parser",
  "confidence",
  "notes",
];

const reportColumns = [
  "date",
  "source_url",
  "capture_timestamp",
  "parser",
  "rows_extracted",
  "confidence",
  "html_path",
];

const miniCatalogColumns = [
  "game_url",
  "game_name",
  "developer",
  "first_seen_date",
  "last_seen_date",
  "best_rank",
  "top_n_appearances",
  "ranking_types",
  "categories",
  "first_source_url",
  "first_capture_timestamp",
  "last_source_url",
  "last_capture_timestamp",
  "listing_play_count_rows",
  "max_listing_play_count_observed",
  "needs_game_page_history",
];

const gamePlayHistoryColumns = [
  "date",
  "game_name",
  "game_url",
  "plays_count_observed",
  "favorites_count_observed",
  "plays_text",
  "favorites_text",
  "metrics_url",
  "capture_timestamp",
  "capture_url",
  "parser",
  "confidence",
  "notes",
];

async function readJsonRows(filePath) {
  try {
    const payload = JSON.parse(await fs.readFile(filePath, "utf8"));
    return payload.rows ?? [];
  } catch (error) {
    if (error.code === "ENOENT") return [];
    throw error;
  }
}

function columnName(indexZeroBased) {
  let n = indexZeroBased + 1;
  let name = "";
  while (n > 0) {
    const rem = (n - 1) % 26;
    name = String.fromCharCode(65 + rem) + name;
    n = Math.floor((n - 1) / 26);
  }
  return name;
}

function literalTextFormula(value) {
  return `="${String(value).replaceAll('"', '""')}"`;
}

function matrixFromRows(columns, rows) {
  return [
    columns,
    ...rows.map((row) => columns.map((column) => {
      const value = row[column] ?? "";
      if (typeof value === "number" || typeof value === "boolean") return value;
      return String(value);
    })),
  ];
}

function styleSheet(sheet, columns, rowCount, tableName) {
  const lastCol = columnName(columns.length - 1);
  const lastRow = Math.max(rowCount + 1, 1);
  const rangeAddress = `A1:${lastCol}${lastRow}`;
  sheet.freezePanes.freezeRows(1);
  sheet.getRange(`A1:${lastCol}1`).format.fill.color = "#F1F3F4";
  sheet.getRange(`A1:${lastCol}1`).format.font.bold = true;
  sheet.getRange(`A1:${lastCol}1`).format.wrapText = true;
  sheet.getRange(rangeAddress).format.borders = { preset: "inside", style: "thin", color: "#E6E6E6" };
  sheet.getRange(rangeAddress).format.verticalAlignment = "top";
  sheet.getRange(rangeAddress).format.wrapText = true;

  columns.forEach((column, index) => {
    const letter = columnName(index);
    let width = 18;
    if (column === "date") width = 14;
    if (column === "game_name") width = 32;
    if (column === "rank_on_date") width = 14;
    if (column === "plays_count_observed" || column === "plays_rank_within_capture") width = 18;
    if (column === "ranking_basis" || column === "plays_rank_scope") width = 26;
    if (column.includes("url") || column === "notes" || column === "html_path") width = 42;
    if (column.includes("timestamp")) width = 20;
    if (column === "ranking_type" || column === "confidence" || column === "parser") width = 18;
    sheet.getRange(`${letter}:${letter}`).format.columnWidth = width;
    if (column.includes("timestamp")) {
      sheet.getRange(`${letter}:${letter}`).format.numberFormat = "0";
      if (lastRow > 1) sheet.getRange(`${letter}2:${letter}${lastRow}`).setNumberFormat("0");
    }
  });

  if (rowCount > 0) {
    const table = sheet.tables.add(rangeAddress, true, tableName);
    table.showFilterButton = true;
    table.showBandedRows = false;
  }
}

function applyTimestampTextFormulas(sheet, columns, rows) {
  void sheet;
  void columns;
  void rows;
}

async function addSheet(workbook, sheetName, columns, rows, tableName) {
  const sheet = workbook.worksheets.add(sheetName);
  const matrix = matrixFromRows(columns, rows);
  const lastCol = columnName(columns.length - 1);
  const lastRow = Math.max(matrix.length, 1);
  sheet.getRange(`A1:${lastCol}${lastRow}`).values = matrix;
  applyTimestampTextFormulas(sheet, columns, rows);
  styleSheet(sheet, columns, rows.length, tableName);
  return sheet;
}

async function main() {
  const rankedPayload = JSON.parse(await fs.readFile(rankedJsonPath, "utf8"));
  const reportPayload = JSON.parse(await fs.readFile(reportJsonPath, "utf8"));
  await fs.mkdir(outputDir, { recursive: true });
  await fs.mkdir(previewDir, { recursive: true });

  const workbook = Workbook.create();
  const rankedRows = rankedPayload.rows ?? [];
  const miniCatalogRows = await readJsonRows(miniCatalogJsonPath);
  const gamePlayHistoryRows = await readJsonRows(gamePlayHistoryJsonPath);
  const reportRows = rankedPayload.sample_reports ?? reportPayload.samples ?? [];

  await addSheet(workbook, "ranked_games", rankedColumns, rankedRows, "ranked_games_table");
  await addSheet(workbook, "mini_catalog", miniCatalogColumns, miniCatalogRows, "mini_catalog_table");
  await addSheet(workbook, "game_play_history", gamePlayHistoryColumns, gamePlayHistoryRows, "game_play_history_table");
  await addSheet(workbook, "extraction_report", reportColumns, reportRows, "extraction_report_table");

  const inspect = await workbook.inspect({
    kind: "workbook,sheet,table",
    maxChars: 8000,
    tableMaxRows: 3,
    tableMaxCols: 8,
  });
  await fs.writeFile(path.join(outputDir, "workbook_inspect.ndjson"), inspect.ndjson);

  const errors = await workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 300 },
    summary: "final formula error scan",
  });
  await fs.writeFile(path.join(outputDir, "formula_error_scan.ndjson"), errors.ndjson);

  for (const [sheetName, columns, rows] of [
    ["ranked_games", rankedColumns, rankedRows],
    ["mini_catalog", miniCatalogColumns, miniCatalogRows],
    ["game_play_history", gamePlayHistoryColumns, gamePlayHistoryRows],
    ["extraction_report", reportColumns, reportRows],
  ]) {
    const lastCol = columnName(columns.length - 1);
    const previewLastRow = Math.min(Math.max(rows.length + 1, 1), 40);
    const preview = await workbook.render({ sheetName, range: `A1:${lastCol}${previewLastRow}`, scale: 1, format: "png" });
    const bytes = new Uint8Array(await preview.arrayBuffer());
    await fs.writeFile(path.join(previewDir, `${sheetName}.png`), bytes);
  }

  const output = await SpreadsheetFile.exportXlsx(workbook);
  const xlsxPath = path.join(outputDir, "kongregate_ranked_games.xlsx");
  await output.save(xlsxPath);
  console.log(JSON.stringify({
    xlsxPath,
    rankedRows: rankedRows.length,
    miniCatalogRows: miniCatalogRows.length,
    gamePlayHistoryRows: gamePlayHistoryRows.length,
    reportRows: reportRows.length,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
