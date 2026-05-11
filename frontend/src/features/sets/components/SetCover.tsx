interface SetCoverProps {
  langCode: string;
  langName: string;
  setId: number;
}

const LANG_GRADIENTS: Record<string, [string, string]> = {
  en: ['#3b82f6', '#6366f1'],
  es: ['#f97316', '#ef4444'],
  fr: ['#3b82f6', '#8b5cf6'],
  de: ['#eab308', '#f97316'],
  ja: ['#ec4899', '#f43f5e'],
  ko: ['#06b6d4', '#3b82f6'],
  zh: ['#ef4444', '#ec4899'],
  pt: ['#22c55e', '#10b981'],
  it: ['#f97316', '#fbbf24'],
  ru: ['#6366f1', '#3b82f6'],
  ar: ['#10b981', '#06b6d4'],
  nl: ['#f97316', '#eab308'],
  pl: ['#ef4444', '#f97316'],
  sv: ['#3b82f6', '#06b6d4'],
  tr: ['#ef4444', '#f97316'],
  uk: ['#eab308', '#3b82f6'],
  hi: ['#f97316', '#ec4899'],
};

const FALLBACK_GRADIENTS: [string, string][] = [
  ['#6366f1', '#8b5cf6'],
  ['#06b6d4', '#3b82f6'],
  ['#f97316', '#eab308'],
  ['#22c55e', '#06b6d4'],
  ['#ec4899', '#f97316'],
  ['#8b5cf6', '#ec4899'],
];

function pickFallback(setId: number): [string, string] {
  return FALLBACK_GRADIENTS[((setId * 2654435761) >>> 0) % FALLBACK_GRADIENTS.length];
}

export function langAccentColor(langCode: string, setId: number): string {
  const code = langCode.toLowerCase().slice(0, 2);
  return (LANG_GRADIENTS[code] ?? pickFallback(setId))[0];
}

export function SetCover({ langCode, langName, setId }: SetCoverProps) {
  const code = langCode.toLowerCase().slice(0, 2);
  const [from, to] = LANG_GRADIENTS[code] ?? pickFallback(setId);

  return (
    <div
      className="h-24 rounded-t-lg flex flex-col items-center justify-center gap-0.5 select-none"
      style={{ background: `linear-gradient(135deg, ${from}, ${to})` }}
    >
      <span className="text-4xl font-black text-white/90 uppercase tracking-wider leading-none">
        {code.toUpperCase()}
      </span>
      <span className="text-[10px] font-semibold text-white/60 uppercase tracking-widest">
        {langName}
      </span>
    </div>
  );
}
