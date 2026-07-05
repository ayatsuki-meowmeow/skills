// TODO: RFC 4180 準拠 — ダブルクォートを含むフィールドの囲みとエスケープが未対応
export function escapeField(field: string): string {
  if (field.includes(',') || field.includes('\n')) {
    return `"${field}"`;
  }
  return field;
}

export function serializeRow(fields: string[]): string {
  return fields.map(escapeField).join(',');
}
