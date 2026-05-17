import { Volume2, X } from 'lucide-react';
import { useState } from 'react';
import { useBrowserZoomScale } from '../hooks/useBrowserZoomScale';

interface MediaPanelProps {
  imageUrl: string | null;
  showSoundIcon: boolean;
  onSoundClick: () => void;
  partOfSpeech?: string | null;
  posColorClass?: string;
  posHexColor?: string;
}

const POS_DEFINITIONS: Record<string, string> = {
  'noun':         'A word that names a person, place, thing, or idea. Answers "who?" or "what?"',
  'verb':         'A word expressing an action or state of being. Answers "what does?" or "what is?"',
  'adjective':    'A word that describes or modifies a noun. Answers "what kind?", "which one?", or "how many?"',
  'adverb':       'A word that modifies a verb, adjective, or another adverb. Answers "how?", "when?", or "where?"',
  'modal verb':   'A helper verb expressing possibility, necessity, or permission — can, must, should, will, etc.',
  'pronoun':      'A word that replaces a noun — he, she, it, they, we, you, who, etc.',
  'preposition':  'A word showing the relationship between a noun and another element — in, on, at, by, with, etc.',
  'conjunction':  'A word that connects words, phrases, or clauses — and, but, or, because, although, etc.',
  'article':      'A word that specifies a noun as definite or indefinite — the, a, an.',
  'interjection': 'A word or phrase expressing a sudden emotion — oh!, wow!, hey!, oops!',
};

const IMAGE_SIZE = 288; // w-72

export function MediaPanel({ imageUrl, showSoundIcon, onSoundClick, partOfSpeech, posColorClass, posHexColor }: MediaPanelProps) {
  const scale = useBrowserZoomScale();
  const margin = (IMAGE_SIZE * (scale - 1)) / 2;
  const [showDef, setShowDef] = useState(false);

  const definition = partOfSpeech ? POS_DEFINITIONS[partOfSpeech.toLowerCase()] : null;
  const glowColor = posHexColor ?? '#888888';

  return (
    <div className="flex flex-col items-center">
      <div
        className="relative mb-4"
        style={{ transform: `scale(${scale})`, margin: `${margin}px` }}
      >
        {imageUrl ? (
          <img
            src={imageUrl}
            alt=""
            className="w-72 h-72 rounded-full object-cover"
          />
        ) : (
          <div className="w-64 h-64 rounded-full bg-muted/60" />
        )}

        {showSoundIcon && (
          <button
            onClick={onSoundClick}
            className="absolute bottom-8 right-2 flex items-center justify-center w-8 h-8 rounded-full bg-background/80 backdrop-blur-sm border border-border shadow-sm hover:bg-background transition-colors"
            aria-label="Replay pronunciation"
          >
            <Volume2 className="w-4 h-4 text-muted-foreground" />
          </button>
        )}

        {partOfSpeech && (
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 flex flex-col items-center">

            {/* Definition card — below the badge */}
            {showDef && definition && (
              <div
                className="absolute bottom-full mb-3 w-80 bg-white rounded-2xl border border-border/20 p-4 text-left z-10"
                style={{ boxShadow: `0 0 0 1px ${glowColor}22, 0 8px 32px 0 ${glowColor}44` }}
              >
                {/* Arrow pointing up */}
                <div
                  className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-4 h-4 bg-white rotate-45 border-r border-b border-border/20"
                  style={{ boxShadow: `2px 2px 4px 0 ${glowColor}22` }}
                />
                <button
                  onClick={(e) => { e.stopPropagation(); setShowDef(false); }}
                  className="absolute top-3 right-3 text-muted-foreground hover:text-foreground transition-colors"
                  aria-label="Close"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
                <p className="text-xs text-navy leading-relaxed pr-4">
                  <span className={`font-bold capitalize ${posColorClass ?? ''}`}>{partOfSpeech}</span>
                  {' — '}{definition}
                </p>
              </div>
            )}

            <span
              onClick={() => setShowDef(v => !v)}
              className={`px-4 py-0.5 bg-background rounded-full text-sm font-semibold tracking-wide capitalize shadow-sm border border-border/40 cursor-pointer select-none transition-opacity hover:opacity-80 ${posColorClass ?? ''}`}
            >
              {partOfSpeech}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
