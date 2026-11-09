/** Gera CSV compatível com planilhas sem interpretar valores como fórmulas. */

function safeCell(value: string | number): string {
  const text = String(value)
  // Excel/LibreOffice: prefixar fórmulas para prevenir CSV injection.
  const sanitized = /^[\\s]*[=+@-]/.test(text) ? "'" + text : text
  return '"' + sanitized.replaceAll('"', '""') + '"'
}

export function csvContent(
  headings: string[],
  rows: Array<Array<string | number>>,
): string {
  return '\uFEFF' + [headings, ...rows].map(
    (row) => row.map(safeCell).join(';')
  ).join('\r\n') + '\r\n'
}
