interface JsonlParseOptions<T> {
  filename?: string;
  validate?: (value: unknown, lineNumber: number) => T;
}

export function parseJsonl<T>(text: string, options: JsonlParseOptions<T> = {}): T[] {
  const values: T[] = [];
  const filename = options.filename ?? "JSONL";

  for (const [index, line] of text.split(/\r?\n/).entries()) {
    const trimmed = line.trim();
    if (!trimmed) {
      continue;
    }

    let value: unknown;
    try {
      value = JSON.parse(trimmed) as unknown;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      throw new Error(`${filename}:line ${index + 1}: invalid JSON: ${message}`);
    }
    if (typeof value !== "object" || value === null || Array.isArray(value)) {
      throw new Error(`${filename}:line ${index + 1}: expected a JSON object`);
    }
    values.push(options.validate ? options.validate(value, index + 1) : value as T);
  }

  return values;
}
