/** Parse / format dashboard pseudo-Python config (mirrors backend config_parse.py). */

export const SEARCH_LIST_KEYS = new Set([
  "search_terms",
  "experience_level",
  "job_type",
  "on_site",
  "companies",
  "location",
  "industry",
  "job_function",
  "job_titles",
  "benefits",
  "commitments",
  "about_company_bad_words",
  "about_company_good_words",
  "bad_words",
]);

function tryParseList(text: string): string[] | null {
  const trimmed = text.trim();
  if (!trimmed.startsWith("[")) return null;
  try {
    const normalized = trimmed.replace(/'/g, '"');
    const parsed = JSON.parse(normalized);
    return Array.isArray(parsed) ? parsed.map(String) : null;
  } catch {
    return null;
  }
}

export function normalizeConfigValue(key: string, value: unknown): unknown {
  if (value === null || value === undefined) {
    return SEARCH_LIST_KEYS.has(key) ? [] : "";
  }
  if (Array.isArray(value)) {
    return value;
  }
  if (typeof value === "string") {
    const text = value.trim();
    if (SEARCH_LIST_KEYS.has(key)) {
      if (text === "[" || text === '["' || text === "']" || text === "") {
        return [];
      }
      const asList = tryParseList(text);
      if (asList) return asList;
      return text ? [text] : [];
    }
  }
  return value;
}

export function parseConfigValue(raw: string, key = ""): unknown {
  const valueStr = raw.trim();
  if (!valueStr) return "";

  if (
    (valueStr.startsWith('"') && valueStr.endsWith('"')) ||
    (valueStr.startsWith("'") && valueStr.endsWith("'"))
  ) {
    const inner = valueStr
      .slice(1, -1)
      .replace(/\\n/g, "\n")
      .replace(/\\"/g, '"');
    if (SEARCH_LIST_KEYS.has(key) || inner.trim().startsWith("[")) {
      const asList = tryParseList(inner);
      if (asList) return asList;
    }
    if (SEARCH_LIST_KEYS.has(key) && (inner.trim() === "[" || inner.trim() === "")) {
      return [];
    }
    return inner;
  }

  const lower = valueStr.toLowerCase();
  if (lower === "true") return true;
  if (lower === "false") return false;

  const asList = tryParseList(valueStr);
  if (asList) return asList;

  if (valueStr === "[" || valueStr === '["') return [];

  if (/^-?\d+$/.test(valueStr)) return Number(valueStr);
  if (/^-?\d+\.\d+$/.test(valueStr)) return Number(valueStr);

  if (SEARCH_LIST_KEYS.has(key)) {
    return valueStr ? [valueStr] : [];
  }
  return valueStr;
}

export function parseConfigContent(content: string): Record<string, unknown> {
  const parsed: Record<string, unknown> = {};
  const lines = content.split("\n");
  let currentKey = "";
  let currentValue = "";
  let inQuotedString = false;
  let quoteChar = '"';

  for (const line of lines) {
    if (!inQuotedString) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) continue;
      if (!line.includes("=")) continue;

      const eq = line.indexOf("=");
      currentKey = line.slice(0, eq).trim();
      const val = line.slice(eq + 1).trim();

      if (val.startsWith('"') || val.startsWith("'")) {
        quoteChar = val[0];
        inQuotedString = true;
        currentValue = val.slice(1);
        if (currentValue.endsWith(quoteChar) && currentValue.length > 0) {
          inQuotedString = false;
          parsed[currentKey] = parseConfigValue(
            quoteChar + currentValue.slice(0, -1) + quoteChar,
            currentKey
          );
        }
      } else {
        parsed[currentKey] = parseConfigValue(val, currentKey);
      }
    } else if (line.endsWith(quoteChar)) {
      inQuotedString = false;
      currentValue += "\n" + line.slice(0, -1);
      parsed[currentKey] = parseConfigValue(
        quoteChar + currentValue + quoteChar,
        currentKey
      );
    } else {
      currentValue += "\n" + line;
    }
  }

  if (inQuotedString && currentKey) {
    parsed[currentKey] = parseConfigValue(
      quoteChar + currentValue + quoteChar,
      currentKey
    );
  }

  for (const [key, value] of Object.entries(parsed)) {
    parsed[key] = normalizeConfigValue(key, value);
  }

  return parsed;
}

export function formatConfigValue(value: unknown): string {
  if (typeof value === "boolean") {
    return value ? "True" : "False";
  }
  if (Array.isArray(value)) {
    return JSON.stringify(value).replace(/"/g, "'");
  }
  if (typeof value === "string") {
    const escaped = value
      .replace(/\\/g, "\\\\")
      .replace(/"/g, '\\"')
      .replace(/\n/g, "\\n");
    return `"${escaped}"`;
  }
  if (value === null || value === undefined) {
    return '""';
  }
  return String(value);
}

export function formatConfigContent(
  category: string,
  data: Record<string, unknown>
): string {
  let out = `################ ${category.toUpperCase()} CONFIGURATION ################\n\n`;
  for (const [key, value] of Object.entries(data)) {
    const normalized = normalizeConfigValue(key, value);
    out += `${key} = ${formatConfigValue(normalized)}\n`;
  }
  return out;
}
