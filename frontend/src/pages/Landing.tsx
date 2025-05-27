import React, { useEffect } from 'react';
import styles from './landing.module.css';

const LingvoPal: React.FC = () => {
    useEffect(() => {
        const handleScroll = () => {
            const navbar = document.querySelector(`.${styles.navbar}`);
            if (window.scrollY > 50) {
                navbar?.classList.add(styles.scrolled);
            } else {
                navbar?.classList.remove(styles.scrolled);
            }
        };

        const menuToggle = document.querySelector(`.${styles.menuToggle}`);
        const navLinks = document.querySelector(`.${styles.navLinks}`);

        const handleMenuToggle = () => {
            navLinks?.classList.toggle(styles.active);
            menuToggle?.classList.toggle(styles.open);

            const spans = menuToggle?.querySelectorAll('span');
            if (spans) {
                if (menuToggle?.classList.contains(styles.open)) {
                    spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
                    spans[1].style.opacity = '0';
                    spans[2].style.transform = 'rotate(-45deg) translate(7px, -7px)';
                } else {
                    spans[0].style.transform = 'none';
                    spans[1].style.opacity = '1';
                    spans[2].style.transform = 'none';
                }
            }
        };

        const handleLinkClick = () => {
            navLinks?.classList.remove(styles.active);
            menuToggle?.classList.remove(styles.open);
            const spans = menuToggle?.querySelectorAll('span');
            if (spans) {
                spans[0].style.transform = 'none';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'none';
            }
        };

        window.addEventListener('scroll', handleScroll);
        menuToggle?.addEventListener('click', handleMenuToggle);
        navLinks?.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', handleLinkClick);
        });

        return () => {
            window.removeEventListener('scroll', handleScroll);
            menuToggle?.removeEventListener('click', handleMenuToggle);
            navLinks?.querySelectorAll('a').forEach(link => {
                link.removeEventListener('click', handleLinkClick);
            });
        };
    }, []);

    return (
        <>
            <nav className={styles.navbar}>
                <div className={`${styles.container} ${styles.navContainer}`}>
                    <div className={styles.navLogo}>
                        <span className={styles.logoContainer}>
                            <span className={styles.logoLingvo}>Lingvo</span><span className={styles.logoPal}>Pal</span>
                        </span>
                    </div>
                    <div className={styles.navLinks}>
                        <a href="#features">Features</a>
                        <a href="#how-it-works">How It Works</a>
                        <a href="#testimonials">Testimonials</a>
                    </div>
                    <div className={styles.navButtons}>
                        <a href="login.html" className={`${styles.btn} ${styles.btnOutline}`}>Log In</a>
                        <a href="signup.html" className={`${styles.btn} ${styles.btnPrimary}`}>Get Started</a>
                    </div>
                    <div className={styles.menuToggle}>
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </nav>

            <section className={styles.hero}>
                <div className={styles.container}>
                    <div className={`${styles.heroContent} ${styles.fadeInUp}`}>
                        <h1>Learn languages the natural way with <span>LingvoPal</span></h1>
                        <p className={`${styles.delay1} ${styles.fadeInUp}`}>Achieve fluency faster with our AI-powered language learning platform. Personalized lessons, interactive flashcards, and conversational practice with our intelligent AI assistant.</p>
                        <a href="signup.html" className={`${styles.btn} ${styles.btnPrimary} ${styles.delay2} ${styles.fadeInUp}`}>Start Learning For Free</a>
                    </div>
                </div>
            </section>

            <section className={`${styles.features} ${styles.section}`} id="features">
                <div className={styles.container}>
                    <div className={styles.sectionHeader}>
                        <h2>Our Unique Features</h2>
                        <p>LingvoPal combines the best language learning techniques with cutting-edge AI technology to create a personalized learning experience.</p>
                    </div>
                    <div className={styles.featuresGrid}>
                        <div className={styles.featureCard}>
                            <div className={styles.featureIcon}>🎮</div>
                            <h3>Smart Flash Cards</h3>
                            <p>Our interactive flash cards use sentences and images for better memorization. Advanced spaced repetition system ensures you remember vocabulary long-term.</p>
                        </div>
                        <div className={styles.featureCard}>
                            <div className={styles.featureIcon}>🤖</div>
                            <h3>AI Language Assistant</h3>
                            <p>Practice conversations with our AI assistant that adapts to your level, provides instant feedback, and helps you improve your speaking and writing skills.</p>
                        </div>
                        <div className={styles.featureCard}>
                            <div className={styles.featureIcon}>📊</div>
                            <h3>Progress Tracking</h3>
                            <p>Detailed statistics show your progress, most common mistakes, and learning patterns to help you optimize your study time.</p>
                        </div>
                        <div className={styles.featureCard}>
                            <div className={styles.featureIcon}>🎯</div>
                            <h3>Personalized Learning</h3>
                            <p>Choose your focus areas (vocabulary, grammar, conversation) and get a customized learning path that adapts to your progress.</p>
                        </div>
                        <div className={styles.featureCard}>
                            <div className={styles.featureIcon}>🌊</div>
                            <h3>Language Immersion</h3>
                            <p>Optional immersion mode where everything is in your target language to accelerate learning and improve comprehension.</p>
                        </div>
                        <div className={styles.featureCard}>
                            <div className={styles.featureIcon}>📱</div>
                            <h3>Learn Anywhere</h3>
                            <p>Access LingvoPal on any device with reminders to help you maintain a consistent study schedule.</p>
                        </div>
                    </div>
                </div>
            </section>

            <section className={`${styles.howItWorks} ${styles.section}`} id="how-it-works">
                <div className={styles.container}>
                    <div className={styles.sectionHeader}>
                        <h2>How LingvoPal Works</h2>
                        <p>Our platform makes language learning effective and enjoyable in just a few simple steps.</p>
                    </div>
                    <div className={styles.steps}>
                        <div className={styles.step}>
                            <div className={styles.stepNumber}>1</div>
                            <h3>Sign Up</h3>
                            <p>Create your account and select your target language and proficiency level.</p>
                        </div>
                        <div className={styles.step}>
                            <div className={styles.stepNumber}>2</div>
                            <h3>Customize</h3>
                            <p>Set your learning goals and preferences to get a personalized learning path.</p>
                        </div>
                        <div className={styles.step}>
                            <div className={styles.stepNumber}>3</div>
                            <h3>Practice</h3>
                            <p>Use flash cards, chat with AI, and complete exercises that adapt to your level.</p>
                        </div>
                        <div className={styles.step}>
                            <div className={styles.stepNumber}>4</div>
                            <h3>Progress</h3>
                            <p>Track your improvement and adjust your learning strategy based on detailed analytics.</p>
                        </div>
                    </div>
                </div>
            </section>

            <section className={`${styles.testimonials} ${styles.section}`} id="testimonials">
                <div className={styles.container}>
                    <div className={styles.sectionHeader}>
                        <h2>What Our Users Say</h2>
                        <p>Join thousands of satisfied learners who have improved their language skills with LingvoPal.</p>
                    </div>
                    <div className={styles.testimonialGrid}>
                        <div className={styles.testimonialCard}>
                            <div className={styles.testimonialText}>LingvoPal's AI assistant made practicing Spanish conversations so much fun! It feels like talking to a patient tutor who never gets tired of correcting my mistakes.</div>
                            <div className={styles.testimonialAuthor}>
                                <div className={styles.authorAvatar}>
                                    <img src="img/avatar1.jpg" alt="Maria Lopez" />
                                </div>
                                <div className={styles.authorInfo}>
                                    <h4>Maria Lopez</h4>
                                    <p>Student, Spain</p>
                                </div>
                            </div>
                        </div>
                        <div className={styles.testimonialCard}>
                            <div className={styles.testimonialText}>The smart flashcards helped me remember French vocabulary faster than any other app I've tried. The progress tracking keeps me motivated!</div>
                            <div className={styles.testimonialAuthor}>
                                <div className={styles.authorAvatar}>
                                    <img src="img/avatar2.jpg" alt="James Carter" />
                                </div>
                                <div className={styles.authorInfo}>
                                    <h4>James Carter</h4>
                                    <p>Teacher, Canada</p>
                                </div>
                            </div>
                        </div>
                        <div className={styles.testimonialCard}>
                            <div className={styles.testimonialText}>I love the immersion mode! It pushed me to think in German, and now I feel much more confident with everyday conversations.</div>
                            <div className={styles.testimonialAuthor}>
                                <div className={styles.authorAvatar}>
                                    <img src="img/avatar3.jpg" alt="Anna Schmidt" />
                                </div>
                                <div className={styles.authorInfo}>
                                    <h4>Anna Schmidt</h4>
                                    <p>Engineer, Germany</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <section className={`${styles.cta} ${styles.section}`}>
                <div className={`${styles.container} ${styles.ctaContainer}`}>
                    <h2>Join LingvoPal Today</h2>
                    <p>Start your language learning journey with a platform designed to make fluency achievable and enjoyable. Sign up now and experience the difference!</p>
                    <a href="signup.html" className={`${styles.btn} ${styles.btnLight}`}>Get Started For Free</a>
                </div>
            </section>

            <footer>
                <div className={styles.container}>
                    <div className={styles.footerGrid}>
                        <div className={styles.footerColumn}>
                            <h3>About LingvoPal</h3>
                            <p>LingvoPal is an AI-powered language learning platform dedicated to helping you achieve fluency through personalized, engaging, and effective methods.</p>
                        </div>
                        <div className={styles.footerColumn}>
                            <h3>Quick Links</h3>
                            <ul className={styles.footerLinks}>
                                <li><a href="#features">Features</a></li>
                                <li><a href="#how-it-works">How It Works</a></li>
                                <li><a href="#testimonials">Testimonials</a></li>
                                <li><a href="pricing.html">Pricing</a></li>
                            </ul>
                        </div>
                        <div className={styles.footerColumn}>
                            <h3>Support</h3>
                            <ul className={styles.footerLinks}>
                                <li><a href="faq.html">FAQ</a></li>
                                <li><a href="contact.html">Contact Us</a></li>
                                <li><a href="terms.html">Terms of Service</a></li>
                                <li><a href="privacy.html">Privacy Policy</a></li>
                            </ul>
                        </div>
                        <div className={styles.footerColumn}>
                            <h3>Connect</h3>
                            <ul className={styles.footerLinks}>
                                <li><a href="blog.html">Blog</a></li>
                                <li><a href="community.html">Community</a></li>
                                <li><a href="careers.html">Careers</a></li>
                            </ul>
                        </div>
                    </div>
                    <div className={styles.footerBottom}>
                        <div className={styles.socialIcons}>
                            <a href="https://facebook.com" className={styles.socialIcon} target="_blank" rel="noopener noreferrer">📘</a>
                            <a href="https://twitter.com" className={styles.socialIcon} target="_blank" rel="noopener noreferrer">🐦</a>
                            <a href="https://instagram.com" className={styles.socialIcon} target="_blank" rel="noopener noreferrer">📷</a>
                            <a href="https://linkedin.com" className={styles.socialIcon} target="_blank" rel="noopener noreferrer">💼</a>
                        </div>
                        <p className={styles.copyright}>&copy; 2025 LingvoPal. All rights reserved.</p>
                    </div>
                </div>
            </footer>
        </>
    );
};

export default LingvoPal;