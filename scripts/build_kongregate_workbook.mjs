import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = path.resolve(".");
const processedPath = path.join(root, "data", "processed", "tables.json");
const outputDir = path.join(root, "outputs", "kongregate_wayback_pilot");
const previewDir = path.join(outputDir, "previews");

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

function rowsForSheet(columns, rows) {
  return [
    columns,
    ...rows.map((row) => columns.map((col) => {
      const value = row[col] ?? "";
      if (typeof value === "number" || typeof value === "boolean") return value;
      return String(value);
    })),
  ];
}

function literalTextFormula(value) {
  return `="${String(value).replaceAll('"', '""')}"`;
}

function setWidths(sheetName, sheet, columns) {
  columns.forEach((column, index) => {
    const letter = columnName(index);
    let width = 18;
    if (column.includes("url") || column.includes("notes") || column.includes("markers") || column.includes("selector")) width = 42;
    if (column.includes("timestamp") || column === "week_start") width = 20;
    if (column.endsWith("_id") || column === "year" || column === "month") width = 14;
    if (column.includes("count") || column.includes("confidence") || column.includes("status")) width = 16;
    sheet.getRange(`${letter}:${letter}`).format.columnWidth = width;
  });
  if (sheetName === "capture_coverage") {
    sheet.getRange("A:A").format.columnWidth = 14;
    sheet.getRange("B:B").format.columnWidth = 42;
  }
}

async function main() {
  const payload = JSON.parse(await fs.readFile(processedPath, "utf8"));
  await fs.mkdir(outputDir, { recursive: true });
  await fs.mkdir(previewDir, { recursive: true });

  const workbook = Workbook.create();
  const sheetNames = Object.keys(payload.columns);

  for (const sheetName of sheetNames) {
    const columns = payload.columns[sheetName];
    const rows = payload.tables[sheetName] ?? [];
    const sheet = workbook.worksheets.add(sheetName);
    const matrix = rowsForSheet(columns, rows);
    const lastCol = columnName(columns.length - 1);
    const lastRow = Math.max(matrix.length, 1);
    const rangeAddress = `A1:${lastCol}${lastRow}`;
    const range = sheet.getRange(rangeAddress);
    columns.forEach((column, index) => {
      if (column.includes("timestamp")) {
        const letter = columnName(index);
        sheet.getRange(`${letter}:${letter}`).format.numberFormat = "@";
      }
    });
    range.values = matrix;
    columns.forEach((column, index) => {
      if (column.includes("timestamp") && rows.length > 0) {
        const letter = columnName(index);
        const formulas = rows.map((row) => {
          const value = row[column] ?? "";
          return [value ? literalTextFormula(value) : ""];
        });
        sheet.getRange(`${letter}2:${letter}${rows.length + 1}`).formulas = formulas;
      }
    });

    sheet.freezePanes.freezeRows(1);
    sheet.showGridLines = true;
    sheet.getRange(`A1:${lastCol}1`).format.fill.color = "#F1F3F4";
    sheet.getRange(`A1:${lastCol}1`).format.font.bold = true;
    sheet.getRange(`A1:${lastCol}1`).format.wrapText = true;
    sheet.getRange(rangeAddress).format.borders = { preset: "inside", style: "thin", color: "#E6E6E6" };
    sheet.getRange(rangeAddress).format.wrapText = true;
    sheet.getRange(rangeAddress).format.verticalAlignment = "top";
    setWidths(sheetName, sheet, columns);

    if (rows.length > 0) {
      const safeTableName = `${sheetName.replace(/[^A-Za-z0-9]/g, "_")}_table`.slice(0, 240);
      const table = sheet.tables.add(rangeAddress, true, safeTableName);
      table.showFilterButton = true;
      table.showBandedRows = false;
    }
  }

  const overview = await workbook.inspect({
    kind: "workbook,sheet,table",
    maxChars: 8000,
    tableMaxRows: 2,
    tableMaxCols: 8,
  });
  await fs.writeFile(path.join(outputDir, "workbook_inspect.ndjson"), overview.ndjson);

  const errors = await workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 300 },
    summary: "final formula error scan",
  });
  await fs.writeFile(path.join(outputDir, "formula_error_scan.ndjson"), errors.ndjson);

  for (const sheetName of sheetNames) {
    const columns = payload.columns[sheetName];
    const rows = payload.tables[sheetName] ?? [];
    const lastCol = columnName(columns.length - 1);
    const previewLastRow = Math.min(Math.max(rows.length + 1, 1), 40);
    const preview = await workbook.render({ sheetName, range: `A1:${lastCol}${previewLastRow}`, scale: 1, format: "png" });
    const bytes = new Uint8Array(await preview.arrayBuffer());
    await fs.writeFile(path.join(previewDir, `${sheetName}.png`), bytes);
  }

  const output = await SpreadsheetFile.exportXlsx(workbook);
  const xlsxPath = path.join(outputDir, "kongregate_wayback_pilot.xlsx");
  await output.save(xlsxPath);
  console.log(JSON.stringify({ xlsxPath, sheets: sheetNames.length }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
