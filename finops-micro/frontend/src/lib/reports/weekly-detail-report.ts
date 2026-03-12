import { formatCompactMoney, formatDateLabel, formatMoney, formatPct, formatPctValue } from "@/lib/format";
import type { DailyResponse, SummaryResponse, TopAccountsResponse, TopServicesResponse } from "@/lib/schemas/finops";

type WeeklyDetailReportPayload = {
  cloud: string;
  from: string;
  to: string;
  currency: "BRL" | "USD";
  summary: SummaryResponse;
  daily: DailyResponse;
  topServices: TopServicesResponse;
  topAccounts: TopAccountsResponse;
};

const PAGE_WIDTH = 1684;
const PAGE_HEIGHT = 1190;
const PDF_WIDTH = 842;
const PDF_HEIGHT = 595;

export function openWeeklyDetailReport(payload: WeeklyDetailReportPayload) {
  const reportPeriod = getReportPeriodLabel(payload.from, payload.to);
  const canvas = renderWeeklyDetailCanvas(payload);
  const dataUrl = canvas.toDataURL("image/jpeg", 0.92);
  const jpegBytes = dataUrlToBytes(dataUrl);
  const pdfBlob = buildSingleImagePdf(jpegBytes, canvas.width, canvas.height);
  const url = URL.createObjectURL(pdfBlob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `relatorio-${reportPeriod.toLowerCase()}-${payload.cloud.toLowerCase()}-${payload.from}-${payload.to}.pdf`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  return true;
}

function renderWeeklyDetailCanvas(payload: WeeklyDetailReportPayload) {
  const canvas = document.createElement("canvas");
  canvas.width = PAGE_WIDTH;
  canvas.height = PAGE_HEIGHT;

  const ctx = canvas.getContext("2d");
  if (!ctx) {
    throw new Error("Nao foi possivel criar o contexto do relatorio.");
  }

  const sidebarWidth = 250;
  const cardGap = 18;
  const contentX = 320;
  const contentWidth = PAGE_WIDTH - contentX - 48;
  const kpiY = 216;
  const panelTopY = 368;
  const panelWidth = (contentWidth - cardGap) / 2;

  ctx.fillStyle = "#dfe5e8";
  ctx.fillRect(0, 0, PAGE_WIDTH, PAGE_HEIGHT);

  drawShadowedCard(ctx, 24, 24, PAGE_WIDTH - 48, PAGE_HEIGHT - 48, 0, "#ffffff");

  const sidebarGradient = ctx.createLinearGradient(24, 24, 24, PAGE_HEIGHT - 24);
  sidebarGradient.addColorStop(0, "#03b659");
  sidebarGradient.addColorStop(0.56, "#008f6a");
  sidebarGradient.addColorStop(1, "#1dbec2");
  ctx.fillStyle = sidebarGradient;
  ctx.fillRect(24, 24, sidebarWidth, PAGE_HEIGHT - 48);

  drawSidebar(ctx, payload, 24, 24, sidebarWidth, PAGE_HEIGHT - 48);

  drawHeader(ctx, payload, contentX, 64, contentWidth);
  drawKpis(ctx, payload, contentX, kpiY, contentWidth);

  drawPanel(ctx, contentX, panelTopY, panelWidth, 274, "Resumo executivo", "KPIs e leitura consolidada da semana.");
  drawOverviewRows(ctx, payload, contentX + 22, panelTopY + 88, panelWidth - 44);

  drawPanel(ctx, contentX + panelWidth + cardGap, panelTopY, panelWidth, 274, "Curva diaria", "Variacao diaria do custo no periodo analisado.");
  drawTrendRows(ctx, payload, contentX + panelWidth + cardGap + 22, panelTopY + 90, panelWidth - 44);

  drawPanel(ctx, contentX, panelTopY + 294, panelWidth, 444, "Servicos dominantes", "Servicos com maior representatividade no recorte.");
  drawRankTable(
    ctx,
    ["Servico", "Share", "Total"],
    payload.topServices.slice(0, 7).map((item) => [item.serviceName, formatPctValue(item.sharePct), formatMoney(item.total, payload.currency)]),
    contentX + 22,
    panelTopY + 294 + 88,
    panelWidth - 44,
    formatMoney(payload.summary.totalWeek, payload.currency),
  );

  drawPanel(ctx, contentX + panelWidth + cardGap, panelTopY + 294, panelWidth, 444, "Entidades prioritarias", "Linked accounts com maior peso no recorte.");
  drawRankTable(
    ctx,
    ["Entidade", "Share", "Total"],
    payload.topAccounts.slice(0, 7).map((item) => [normalizeAccountLabel(item.linkedAccount), formatPctValue(item.sharePct), formatMoney(item.total, payload.currency)]),
    contentX + panelWidth + cardGap + 22,
    panelTopY + 294 + 88,
    panelWidth - 44,
    formatMoney(payload.summary.totalWeek, payload.currency),
  );

  ctx.fillStyle = "#5c6771";
  ctx.font = "700 16px 'Segoe UI', Arial, sans-serif";
  ctx.fillText("GRUPO ALGAR | TIC | ENTRETENIMENTO | AGRO", contentX, PAGE_HEIGHT - 42);

  return canvas;
}

function drawSidebar(
  ctx: CanvasRenderingContext2D,
  payload: WeeklyDetailReportPayload,
  x: number,
  y: number,
  width: number,
  height: number,
) {
  const status = getTrafficLightStatus(payload);
  const sidebarCenterX = x + width / 2;

  ctx.fillStyle = "#ffffff";
  ctx.font = "800 52px 'Segoe UI', Arial, sans-serif";
  ctx.textAlign = "center";
  ctx.fillText("Algar", sidebarCenterX, y + 106);

  ctx.font = "800 28px 'Segoe UI', Arial, sans-serif";
  ctx.fillText("GOVERNANÇA", sidebarCenterX, y + 152);
  ctx.fillText("DE TI", sidebarCenterX, y + 186);
  ctx.textAlign = "left";

  drawSidebarLabel(ctx, "VISAO GERAL", x, y + 244, width);
  drawTrafficLight(ctx, x + width / 2, y + 394, status);
  drawSidebarLabel(ctx, "DESTAQUES", x, y + 598, width);

  ctx.fillStyle = "#ffffff";
  ctx.font = "800 44px 'Segoe UI', Arial, sans-serif";
  ctx.textAlign = "center";
  ctx.fillText(payload.cloud.toUpperCase(), sidebarCenterX, y + height - 178);
  ctx.font = "700 26px 'Segoe UI', Arial, sans-serif";
  ctx.fillText("Governança", sidebarCenterX, y + height - 132);
  ctx.fillText("de TI", sidebarCenterX, y + height - 98);
  ctx.textAlign = "left";
}

function drawHeader(ctx: CanvasRenderingContext2D, payload: WeeklyDetailReportPayload, x: number, y: number, width: number) {
  const reportPeriod = getReportPeriodLabel(payload.from, payload.to);
  drawPill(ctx, x, y - 4, 208, 36, "#e7f6f1", "#0a8d6c", `${payload.cloud.toUpperCase()} | VISÃO ${reportPeriod.toUpperCase()}`, 15);

  ctx.fillStyle = "#005c4b";
  ctx.font = "900 68px 'Segoe UI', Arial, sans-serif";
  ctx.fillText(`Relatorio ${reportPeriod}`, x, y + 92);

  ctx.font = "800 44px 'Segoe UI', Arial, sans-serif";
  ctx.fillStyle = "#0b7a66";
  ctx.fillText(`${payload.cloud.toUpperCase()} | ${formatDateRange(payload.from, payload.to)}`, x, y + 148);

  ctx.strokeStyle = "#cfe3dc";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(x, y + 170);
  ctx.lineTo(x + width - 210, y + 170);
  ctx.stroke();

  ctx.font = "700 20px 'Segoe UI', Arial, sans-serif";
  ctx.fillStyle = "#61717a";
  ctx.fillText(`Origem: Visao detalhada ${reportPeriod.toLowerCase()} | Moeda ${payload.currency} | Janela ${payload.from} a ${payload.to}`, x, y + 202);

  ctx.textAlign = "right";
  ctx.fillStyle = "#005c4b";
  ctx.font = "900 58px 'Segoe UI', Arial, sans-serif";
  ctx.fillText("Algar", x + width, y + 76);
  ctx.font = "700 18px 'Segoe UI', Arial, sans-serif";
  ctx.fillStyle = "#0b7a66";
  ctx.fillText("Governanca de TI", x + width, y + 106);
  ctx.textAlign = "left";
}

function drawKpis(ctx: CanvasRenderingContext2D, payload: WeeklyDetailReportPayload, x: number, y: number, width: number) {
  const cards = [
    ["Meta de Consumo Mes", formatCompactMoney(payload.summary.budgetMonth ?? 0, payload.currency)],
    ["Consumo do Mes", formatCompactMoney(payload.summary.monthTotal, payload.currency)],
    ["Meta de Consumo Anual", formatCompactMoney(payload.summary.budgetYear ?? 0, payload.currency)],
    ["Consumo Total do Ano", formatCompactMoney(payload.summary.yearTotal, payload.currency)],
    ["Tendencia", formatPct(payload.summary.deltaWeek)],
  ] as const;

  const gap = 18;
  const cardWidth = (width - gap * 4) / 5;

  cards.forEach(([label, value], index) => {
    const cardX = x + index * (cardWidth + gap);
    drawShadowedCard(ctx, cardX, y, cardWidth, 124, 14, "#f8fbfa", "#7eb0a4");

    ctx.fillStyle = "#6c7177";
    ctx.font = "800 18px 'Segoe UI', Arial, sans-serif";
    drawCenteredWrappedText(ctx, label, cardX + cardWidth / 2, y + 30, cardWidth - 28, 22);

    ctx.fillStyle = "#50555c";
    ctx.font = "800 30px 'Segoe UI', Arial, sans-serif";
    drawCenteredWrappedText(ctx, value, cardX + cardWidth / 2, y + 88, cardWidth - 28, 30);
  });
}

function drawOverviewRows(ctx: CanvasRenderingContext2D, payload: WeeklyDetailReportPayload, x: number, y: number, width: number) {
  const reportPeriod = getReportPeriodLabel(payload.from, payload.to);
  const rows = [
    [`Consumo ${reportPeriod.toLowerCase()}`, formatMoney(payload.summary.totalWeek, payload.currency)],
    ["Media diaria", formatMoney(payload.summary.avgDaily, payload.currency)],
    ["Pico diario", `${formatDateLabel(payload.summary.peakDay.date)} | ${formatMoney(payload.summary.peakDay.amount, payload.currency)}`],
    ["Maior servico", payload.topServices[0] ? `${payload.topServices[0].serviceName} | ${formatPctValue(payload.topServices[0].sharePct)}` : "N/A"],
    ["Maior entidade", payload.topAccounts[0] ? `${normalizeAccountLabel(payload.topAccounts[0].linkedAccount)} | ${formatPctValue(payload.topAccounts[0].sharePct)}` : "N/A"],
  ] as const;

  rows.forEach(([label, value], index) => {
    const rowY = y + index * 34;
    ctx.strokeStyle = "#d6e3df";
    ctx.beginPath();
    ctx.moveTo(x, rowY + 26);
    ctx.lineTo(x + width, rowY + 26);
    ctx.stroke();

    ctx.fillStyle = "#20323d";
    ctx.font = "400 17px 'Segoe UI', Arial, sans-serif";
    ctx.fillText(label, x, rowY + 18);

    ctx.fillStyle = "#005c4b";
    ctx.font = "800 17px 'Segoe UI', Arial, sans-serif";
    ctx.fillText(value, x + 230, rowY + 18);
  });
}

function drawTrendRows(ctx: CanvasRenderingContext2D, payload: WeeklyDetailReportPayload, x: number, y: number, width: number) {
  const rows = payload.daily.slice(0, 7);
  const peak = Math.max(...rows.map((item) => item.total), 0);

  rows.forEach((item, index) => {
    const rowY = y + index * 26;
    const barX = x + 144;
    const barWidth = width - 320;
    const fillWidth = peak > 0 ? Math.max((item.total / peak) * barWidth, 14) : 0;

    ctx.fillStyle = "#20323d";
    ctx.font = "800 17px 'Segoe UI', Arial, sans-serif";
    ctx.fillText(formatDateLabel(item.date), x, rowY + 16);

    roundRectPath(ctx, barX, rowY, barWidth, 20, 10);
    ctx.fillStyle = "#dce9e5";
    ctx.fill();

    roundRectPath(ctx, barX, rowY, fillWidth, 20, 10);
    const fillGradient = ctx.createLinearGradient(barX, rowY, barX + barWidth, rowY);
    fillGradient.addColorStop(0, "#0a8d6c");
    fillGradient.addColorStop(1, "#10b5a9");
    ctx.fillStyle = fillGradient;
    ctx.fill();

    ctx.textAlign = "right";
    ctx.fillStyle = "#005c4b";
    ctx.font = "800 17px 'Segoe UI', Arial, sans-serif";
    ctx.fillText(formatMoney(item.total, payload.currency), x + width, rowY + 17);
    ctx.textAlign = "left";
  });
}

function drawRankTable(
  ctx: CanvasRenderingContext2D,
  headers: [string, string, string],
  rows: string[][],
  x: number,
  y: number,
  width: number,
  totalValue: string,
) {
  ctx.fillStyle = "#6b7480";
  ctx.font = "800 15px 'Segoe UI', Arial, sans-serif";
  ctx.fillText(headers[0], x, y);

  ctx.textAlign = "right";
  ctx.fillText(headers[1], x + width - 174, y);
  ctx.fillText(headers[2], x + width, y);
  ctx.textAlign = "left";

  rows.forEach((row, index) => {
    const rowY = y + 34 + index * 36;
    ctx.strokeStyle = "#d6e3df";
    ctx.beginPath();
    ctx.moveTo(x, rowY + 16);
    ctx.lineTo(x + width, rowY + 16);
    ctx.stroke();

    ctx.fillStyle = "#20323d";
    ctx.font = "400 17px 'Segoe UI', Arial, sans-serif";
    drawWrappedText(ctx, row[0], x, rowY, width - 270, 20, 2);

    ctx.fillStyle = "#005c4b";
    ctx.font = "800 17px 'Segoe UI', Arial, sans-serif";
    ctx.textAlign = "right";
    ctx.fillText(row[1], x + width - 174, rowY);
    ctx.fillText(row[2], x + width, rowY);
    ctx.textAlign = "left";
  });

  const totalY = y + 34 + rows.length * 36 + 6;
  ctx.strokeStyle = "#8eb8ad";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(x, totalY + 10);
  ctx.lineTo(x + width, totalY + 10);
  ctx.stroke();

  ctx.fillStyle = "#4d5c68";
  ctx.font = "800 18px 'Segoe UI', Arial, sans-serif";
  ctx.fillText("Total do periodo", x, totalY + 42);

  ctx.fillStyle = "#005c4b";
  ctx.textAlign = "right";
  ctx.fillText("100.0%", x + width - 174, totalY + 42);
  ctx.fillText(totalValue, x + width, totalY + 42);
  ctx.textAlign = "left";
}

function drawPanel(ctx: CanvasRenderingContext2D, x: number, y: number, width: number, height: number, title: string, subtitle: string) {
  drawShadowedCard(ctx, x, y, width, height, 16, "#f8fbfa", "#7eb0a4");
  ctx.fillStyle = "#4d5c68";
  ctx.font = "800 26px 'Segoe UI', Arial, sans-serif";
  ctx.fillText(title, x + 22, y + 40);
  ctx.fillStyle = "#70808a";
  ctx.font = "400 17px 'Segoe UI', Arial, sans-serif";
  ctx.fillText(subtitle, x + 22, y + 66);
}

function drawSidebarLabel(ctx: CanvasRenderingContext2D, text: string, x: number, y: number, width: number) {
  const labelWidth = 180;
  const labelX = x + (width - labelWidth) / 2;

  ctx.fillStyle = "#3f4143";
  ctx.fillRect(labelX - 34, y - 18, 20, 32);
  ctx.fillStyle = "#ffffff";
  ctx.font = "800 24px 'Segoe UI', Arial, sans-serif";
  ctx.textAlign = "center";
  ctx.fillText(text, labelX + labelWidth / 2 + 8, y + 6);
  ctx.textAlign = "left";
}

function drawTrafficLight(ctx: CanvasRenderingContext2D, x: number, y: number, status: "green" | "yellow" | "red") {
  ctx.fillStyle = "#5a5e62";
  ctx.fillRect(x - 28, y - 78, 56, 156);

  [
    [status === "green" ? "#43c653" : "#5f666b", -42],
    [status === "yellow" ? "#ffee00" : "#5f666b", 0],
    [status === "red" ? "#ff3b30" : "#5f666b", 42],
  ].forEach(([color, offset]) => {
    ctx.beginPath();
    ctx.arc(x, y + Number(offset), 22, 0, Math.PI * 2);
    ctx.fillStyle = String(color);
    ctx.fill();
    ctx.lineWidth = 5;
    ctx.strokeStyle = "#004e43";
    ctx.stroke();
  });
}

function drawShadowedCard(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  height: number,
  radius: number,
  fill: string,
  stroke = "",
) {
  ctx.save();
  ctx.shadowColor = "rgba(24, 39, 75, 0.12)";
  ctx.shadowBlur = 22;
  ctx.shadowOffsetY = 8;
  roundRectPath(ctx, x, y, width, height, radius);
  ctx.fillStyle = fill;
  ctx.fill();
  ctx.restore();

  if (stroke) {
    roundRectPath(ctx, x, y, width, height, radius);
    ctx.lineWidth = 2;
    ctx.strokeStyle = stroke;
    ctx.stroke();
  }
}

function roundRectPath(ctx: CanvasRenderingContext2D, x: number, y: number, width: number, height: number, radius: number) {
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.arcTo(x + width, y, x + width, y + height, radius);
  ctx.arcTo(x + width, y + height, x, y + height, radius);
  ctx.arcTo(x, y + height, x, y, radius);
  ctx.arcTo(x, y, x + width, y, radius);
  ctx.closePath();
}

function drawWrappedText(
  ctx: CanvasRenderingContext2D,
  text: string,
  x: number,
  y: number,
  maxWidth: number,
  lineHeight: number,
  maxLines = 3,
) {
  const lines = splitLines(ctx, text, maxWidth).slice(0, maxLines);
  lines.forEach((line, index) => ctx.fillText(line, x, y + index * lineHeight));
}

function drawPill(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  height: number,
  fill: string,
  textColor: string,
  text: string,
  fontSize: number,
) {
  roundRectPath(ctx, x, y, width, height, height / 2);
  ctx.fillStyle = fill;
  ctx.fill();
  ctx.fillStyle = textColor;
  ctx.font = `800 ${fontSize}px 'Segoe UI', Arial, sans-serif`;
  ctx.textAlign = "center";
  ctx.fillText(text, x + width / 2, y + height / 2 + fontSize / 3 - 1);
  ctx.textAlign = "left";
}

function drawCenteredWrappedText(
  ctx: CanvasRenderingContext2D,
  text: string,
  centerX: number,
  y: number,
  maxWidth: number,
  lineHeight: number,
) {
  const lines = splitLines(ctx, text, maxWidth);
  ctx.textAlign = "center";
  lines.forEach((line, index) => ctx.fillText(line, centerX, y + index * lineHeight));
  ctx.textAlign = "left";
}

function splitLines(ctx: CanvasRenderingContext2D, text: string, maxWidth: number) {
  const words = text.split(/\s+/).filter(Boolean);
  const lines: string[] = [];
  let current = "";

  words.forEach((word) => {
    const candidate = current ? `${current} ${word}` : word;
    if (ctx.measureText(candidate).width <= maxWidth || !current) {
      current = candidate;
      return;
    }
    lines.push(current);
    current = word;
  });

  if (current) {
    lines.push(current);
  }

  return lines;
}

function formatDateRange(from: string, to: string) {
  return `${formatDateLabel(from)} a ${formatDateLabel(to)}`;
}

function getReportPeriodLabel(from: string, to: string): "Semanal" | "Mensal" {
  return getPeriodDayCount(from, to) > 7 ? "Mensal" : "Semanal";
}

function getPeriodDayCount(from: string, to: string): number {
  const fromDate = new Date(`${from}T00:00:00Z`);
  const toDate = new Date(`${to}T00:00:00Z`);
  if (Number.isNaN(fromDate.getTime()) || Number.isNaN(toDate.getTime())) {
    return 0;
  }
  return Math.max(Math.round((toDate.getTime() - fromDate.getTime()) / 86_400_000) + 1, 0);
}

function normalizeAccountLabel(value: string) {
  return value.replace(/\s*\([0-9a-fA-F-]{8,}\)\s*/g, "").trim();
}

function getTrafficLightStatus(payload: WeeklyDetailReportPayload) {
  const target = getPeriodTarget(payload);
  const diff = payload.summary.totalWeek - target;
  const epsilon = 0.01;

  if (Math.abs(diff) <= epsilon) {
    return "yellow";
  }
  if (diff > 0) {
    return "red";
  }
  return "green";
}

function getPeriodTarget(payload: WeeklyDetailReportPayload) {
  const budgetMonth = payload.summary.budgetMonth ?? 0;
  if (budgetMonth <= 0) {
    return payload.summary.totalWeek;
  }

  const fromDate = new Date(`${payload.from}T00:00:00`);
  const toDate = new Date(`${payload.to}T00:00:00`);
  const periodDays = Math.max(Math.round((toDate.getTime() - fromDate.getTime()) / 86_400_000) + 1, 1);
  const monthDays = new Date(fromDate.getFullYear(), fromDate.getMonth() + 1, 0).getDate();

  return (budgetMonth / monthDays) * periodDays;
}

function dataUrlToBytes(dataUrl: string) {
  const base64 = dataUrl.split(",")[1] ?? "";
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return bytes;
}

function buildSingleImagePdf(imageBytes: Uint8Array, imageWidth: number, imageHeight: number) {
  const encoder = new TextEncoder();
  const parts: Uint8Array[] = [];
  const offsets: number[] = [0];
  let position = 0;

  const pushString = (value: string) => {
    const bytes = encoder.encode(value);
    parts.push(bytes);
    position += bytes.length;
  };

  const pushBytes = (value: Uint8Array) => {
    parts.push(value);
    position += value.length;
  };

  pushString("%PDF-1.4\n");

  const objectStart = (id: number) => {
    offsets[id] = position;
    pushString(`${id} 0 obj\n`);
  };

  const objectEnd = () => pushString("\nendobj\n");

  objectStart(1);
  pushString("<< /Type /Catalog /Pages 2 0 R >>");
  objectEnd();

  objectStart(2);
  pushString("<< /Type /Pages /Kids [3 0 R] /Count 1 >>");
  objectEnd();

  objectStart(3);
  pushString(
    `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${PDF_WIDTH} ${PDF_HEIGHT}] /Resources << /XObject << /Im0 5 0 R >> >> /Contents 4 0 R >>`,
  );
  objectEnd();

  const contentStream = encoder.encode(`q\n${PDF_WIDTH} 0 0 ${PDF_HEIGHT} 0 0 cm\n/Im0 Do\nQ`);
  objectStart(4);
  pushString(`<< /Length ${contentStream.length} >>\nstream\n`);
  pushBytes(contentStream);
  pushString("\nendstream");
  objectEnd();

  objectStart(5);
  pushString(
    `<< /Type /XObject /Subtype /Image /Width ${imageWidth} /Height ${imageHeight} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${imageBytes.length} >>\nstream\n`,
  );
  pushBytes(imageBytes);
  pushString("\nendstream");
  objectEnd();

  const xrefOffset = position;
  pushString("xref\n0 6\n");
  pushString("0000000000 65535 f \n");
  for (let index = 1; index <= 5; index += 1) {
    pushString(`${String(offsets[index]).padStart(10, "0")} 00000 n \n`);
  }
  pushString(`trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`);

  return new Blob(parts, { type: "application/pdf" });
}
