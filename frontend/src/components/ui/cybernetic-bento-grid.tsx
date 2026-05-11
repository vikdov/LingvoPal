import { useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';

interface BentoItemProps {
  className?: string;
  style?: React.CSSProperties;
  children: React.ReactNode;
}

export const BentoItem = ({ className, style, children }: BentoItemProps) => {
  const itemRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const item = itemRef.current;
    if (!item) return;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = item.getBoundingClientRect();
      item.style.setProperty('--mouse-x', `${e.clientX - rect.left}px`);
      item.style.setProperty('--mouse-y', `${e.clientY - rect.top}px`);
    };

    item.addEventListener('mousemove', handleMouseMove);
    return () => item.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div ref={itemRef} className={cn('bento-item', className)} style={style}>
      {children}
    </div>
  );
};

export const BentoHoverItem = ({ className, style, children }: BentoItemProps) => {
  const itemRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const item = itemRef.current;
    if (!item) return;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = item.getBoundingClientRect();
      item.style.setProperty('--mouse-x', `${e.clientX - rect.left}px`);
      item.style.setProperty('--mouse-y', `${e.clientY - rect.top}px`);
    };

    item.addEventListener('mousemove', handleMouseMove);
    return () => item.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div ref={itemRef} className={cn('bento-hover-item', className)} style={style}>
      {children}
    </div>
  );
};

export const CyberneticBentoGrid = () => {
  return (
    <div className="flex justify-center px-6 py-20">
      <div className="w-full max-w-6xl">
        <h1 className="text-4xl sm:text-5xl font-bold text-foreground text-center mb-8">Core Features</h1>
        <div className="bento-grid">
          <BentoItem className="col-span-2 row-span-2 flex flex-col justify-between">
            <div>
              <h2 className="text-2xl font-bold text-foreground">Real-time Analytics</h2>
              <p className="mt-2 text-muted-foreground">Monitor your application's performance with up-to-the-second data streams and visualizations.</p>
            </div>
            <div className="mt-4 h-48 bg-muted rounded-lg flex items-center justify-center text-muted-foreground">
              Chart Placeholder
            </div>
          </BentoItem>
          <BentoItem>
            <h2 className="text-xl font-bold text-foreground">Global CDN</h2>
            <p className="mt-2 text-muted-foreground text-sm">Deliver content at lightning speed, no matter where your users are.</p>
          </BentoItem>
          <BentoItem>
            <h2 className="text-xl font-bold text-foreground">Secure Auth</h2>
            <p className="mt-2 text-muted-foreground text-sm">Enterprise-grade authentication and user management built-in.</p>
          </BentoItem>
          <BentoItem className="row-span-2">
            <h2 className="text-xl font-bold text-foreground">Automated Backups</h2>
            <p className="mt-2 text-muted-foreground text-sm">Your data is always safe with automated, redundant backups.</p>
          </BentoItem>
          <BentoItem className="col-span-2">
            <h2 className="text-xl font-bold text-foreground">Serverless Functions</h2>
            <p className="mt-2 text-muted-foreground text-sm">Run your backend code without managing servers. Scale infinitely with ease.</p>
          </BentoItem>
          <BentoItem>
            <h2 className="text-xl font-bold text-foreground">CLI Tool</h2>
            <p className="mt-2 text-muted-foreground text-sm">Manage your entire infrastructure from the command line.</p>
          </BentoItem>
        </div>
      </div>
    </div>
  );
};
