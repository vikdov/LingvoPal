import { LandingNav } from '../components/LandingNav';
import { Hero } from '../components/Hero';
import { HowItWorks } from '../components/HowItWorks';
import { DemoSection } from '../components/DemoSection';
import { ObjectionHandler } from '../components/ObjectionHandler';
import { Features } from '../components/Features';
import { WhyDifferent } from '../components/WhyDifferent';
import { CommunitySection } from '../components/CommunitySection';
import { ProgressSection } from '../components/ProgressSection';
import { CallToAction } from '../components/CallToAction';
import { LandingFooter } from '../components/LandingFooter';

export function LandingView() {
  return (
    <div>
      <LandingNav />
      <main>
        <Hero />
        <HowItWorks />
        <DemoSection />
        <ObjectionHandler />
        <Features />
        <WhyDifferent />
        <CommunitySection />
        <ProgressSection />
        <CallToAction />
      </main>
      <LandingFooter />
    </div>
  );
}
