// frontend/src/features/sets/utils/cefrMapping.ts

export function mapCefrToValue(cefrLevel: string | null): string {
  if (!cefrLevel) return '';

  const mapping: Record<string, string> = {
    A1: '1',
    A2: '2',
    B1: '3',
    B2: '4',
    C1: '5',
    C2: '6',
  };

  return mapping[cefrLevel] || '';
}
