import type { ReactNode } from 'react';
import { GithubIcon, MailIcon, TwitterIcon } from 'lucide-react';
import { LingvoLogo } from '@/components/LingvoLogo';

interface FooterSection {
  title: string;
  links: Array<{ name: string; href: string }>;
}

interface SocialLink {
  icon: ReactNode;
  href: string;
  label: string;
}

interface LegalLink {
  name: string;
  href: string;
}

interface LandingFooterProps {
  logo?: ReactNode;
  sections?: FooterSection[];
  description?: string;
  socialLinks?: SocialLink[];
  copyright?: string;
  legalLinks?: LegalLink[];
}

const defaultSections: FooterSection[] = [
  {
    title: 'Product',
    links: [
      { name: 'How it works', href: '#how-it-works' },
      { name: 'Features', href: '#features' },
      { name: 'Roadmap', href: '#roadmap' },
      { name: 'Changelog', href: '#changelog' },
    ],
  },
  {
    title: 'Company',
    links: [
      { name: 'About', href: '/about' },
      { name: 'Privacy Policy', href: '/privacy' },
      { name: 'Terms of Service', href: '/terms' },
    ],
  },
  {
    title: 'Resources',
    links: [
      { name: 'Documentation', href: '/docs' },
      { name: 'Self-hosting', href: '/docs/self-host' },
    ],
  },
];

const defaultSocialLinks: SocialLink[] = [
  { icon: <GithubIcon className="size-5" />, href: 'https://github.com', label: 'GitHub' },
  { icon: <TwitterIcon className="size-5" />, href: 'https://twitter.com', label: 'Twitter' },
  { icon: <MailIcon className="size-5" />, href: 'mailto:mr.dovhoshyia@gmail.com', label: 'Contact' },
];

const defaultLegalLinks: LegalLink[] = [
  { name: 'Terms and Conditions', href: '/terms' },
  { name: 'Privacy Policy', href: '/privacy' },
];

export const LandingFooter = ({
  logo = <LingvoLogo className="h-8 w-auto" />,
  sections = defaultSections,
  description = 'Writing-first vocabulary practice. Active recall. Spaced repetition. No tricks.',
  socialLinks = defaultSocialLinks,
  copyright = `© ${new Date().getFullYear()} LingvoPal. All rights reserved.`,
  legalLinks = defaultLegalLinks,
}: LandingFooterProps) => {
  return (
    <section className="py-32">
      <div className="container mx-auto">
        <div className="flex w-full flex-col justify-between gap-10 lg:flex-row lg:items-start lg:text-left">
          <div className="flex w-full flex-col justify-between gap-6 lg:items-start">
            <div className="flex items-center gap-2 lg:justify-start">
              {logo}
            </div>
            <p className="max-w-[70%] text-sm text-muted-foreground">
              {description}
            </p>
            <ul className="flex items-center space-x-6 text-muted-foreground">
              {socialLinks.map((social, idx) => (
                <li key={idx} className="font-medium hover:text-primary">
                  <a href={social.href} aria-label={social.label}>
                    {social.icon}
                  </a>
                </li>
              ))}
            </ul>
          </div>
          <div className="grid w-full gap-6 md:grid-cols-3 lg:gap-20">
            {sections.map((section, sectionIdx) => (
              <div key={sectionIdx}>
                <h3 className="mb-4 font-bold">{section.title}</h3>
                <ul className="space-y-3 text-sm text-muted-foreground">
                  {section.links.map((link, linkIdx) => (
                    <li key={linkIdx} className="font-medium hover:text-primary">
                      <a href={link.href}>{link.name}</a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
        <div className="mt-8 flex flex-col justify-between gap-4 border-t py-8 text-xs font-medium text-muted-foreground md:flex-row md:items-center md:text-left">
          <p className="order-2 lg:order-1">{copyright}</p>
          <ul className="order-1 flex flex-col gap-2 md:order-2 md:flex-row">
            {legalLinks.map((link, idx) => (
              <li key={idx} className="hover:text-primary">
                <a href={link.href}>{link.name}</a>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
};
