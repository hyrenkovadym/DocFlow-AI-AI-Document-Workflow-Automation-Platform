import clsx from "clsx";

export function cn(...inputs: Array<string | false | null | undefined>): string {
  return clsx(inputs);
}

export function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export function formatConfidence(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "n/a";
  }
  return value.toFixed(2);
}

export function safeStringify(input: unknown): string {
  try {
    return JSON.stringify(input, null, 2);
  } catch {
    return "{}";
  }
}
