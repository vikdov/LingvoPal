import React, { useEffect } from 'react';
import styles from './footer.module.css';

const Footer: React.FC = () => {
    useEffect(() => {
        const handleScroll = () => {
        const footer = document.querySelector(`.${styles.footer}`);
        if (footer) {
            footer.classList.toggle(styles.visible, window.scrollY + window.innerHeight >= document.body.offsetHeight);
        }
        };
    
        window.addEventListener('scroll', handleScroll);
        return () => {
        window.removeEventListener('scroll', handleScroll);
        };
    }, []);
    
    return (
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
    );
    }
export default Footer;