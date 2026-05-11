import { Volume2 } from 'lucide-react';

interface MediaPanelProps {
  imageUrl: string | null;
  showSoundIcon: boolean;
  onSoundClick: () => void;
}

export function MediaPanel({ imageUrl, showSoundIcon, onSoundClick }: MediaPanelProps) {
  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt=""
            className="w-56 h-56 rounded-full object-cover border border-border"
          />
        ) : (
          <div className="w-56 h-56 rounded-full bg-muted" />
        )}

        {showSoundIcon && (
          <button
            onClick={onSoundClick}
            className="absolute bottom-2 right-2 flex items-center justify-center w-8 h-8 rounded-full bg-background/80 backdrop-blur-sm border border-border shadow-sm hover:bg-background transition-colors"
            aria-label="Replay pronunciation"
          >
            <Volume2 className="w-4 h-4 text-muted-foreground" />
          </button>
        )}
      </div>
    </div>
  );
}
