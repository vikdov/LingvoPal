import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/landing.css';
import { useAuth } from '../context/AuthContext';
import LanguageSelector from '../components/LanguageSelector';

const Dashboard = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const menuToggleRef = useRef(null);
    const navLinksRef = useRef(null);

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    useEffect(() => {
        // Navbar scroll effect
        const handleScroll = () => {
            const navbar = document.querySelector('.navbar');
            if (navbar) {
                if (window.scrollY > 50) {
                    navbar.classList.add('scrolled');
                } else {
                    navbar.classList.remove('scrolled');
                }
            }
        };

        // Mobile menu toggle
        const handleMenuToggle = () => {
            if (navLinksRef.current && menuToggleRef.current) {
                navLinksRef.current.classList.toggle('active');
                menuToggleRef.current.classList.toggle('open');

                // Animate hamburger menu
                const spans = menuToggleRef.current.querySelectorAll('span');
                if (menuToggleRef.current.classList.contains('open')) {
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

        // Set up event listeners
        window.addEventListener('scroll', handleScroll);

        if (menuToggleRef.current) {
            menuToggleRef.current.addEventListener('click', handleMenuToggle);
        }

        // Close mobile menu when clicking a link
        const handleNavLinkClick = () => {
            if (navLinksRef.current && menuToggleRef.current) {
                navLinksRef.current.classList.remove('active');
                menuToggleRef.current.classList.remove('open');

                const spans = menuToggleRef.current.querySelectorAll('span');
                spans[0].style.transform = 'none';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'none';
            }
        };

        const links = navLinksRef.current?.querySelectorAll('a') || [];
        links.forEach(link => {
            link.addEventListener('click', handleNavLinkClick);
        });

        // Cleanup function
        return () => {
            window.removeEventListener('scroll', handleScroll);

            if (menuToggleRef.current) {
                menuToggleRef.current.removeEventListener('click', handleMenuToggle);
            }

            links.forEach(link => {
                link.removeEventListener('click', handleNavLinkClick);
            });
        };
    }, []);

    return (
        <>
        <nav className="navbar">
        <div className="container nav-container">
        <div className="nav-logo">
        <span className="logo-container">
        <span className="logo-lingvo">Lingvo</span><span className="logo-pal">Pal</span>
        </span>
        </div>
        <div className="nav-links" ref={navLinksRef}>
        <a href="#features">Features</a>
        <a href="#how-it-works">How It Works</a>
        <a href="#testimonials">Testimonials</a>
        </div>
        <div className="nav-buttons">
        {user ? (
            <button onClick={handleLogout} className="btn btn-outline">Log Out</button>
        ) : (
            <>
            <a href="/login" className="btn btn-outline">Log In</a>
            <a href="/signup" className="btn btn-primary">Get Started</a>
            </>
        )}
        </div>
        <div className="menu-toggle" ref={menuToggleRef}>
        <span></span>
        <span></span>
        <span></span>
        </div>
        </div>
        </nav>

        <section className="hero">
        <div className="container">
        <div className="hero-content fade-in-up">
        <h1>Learn languages the natural way with <span>LingvoPal</span></h1>
        <p className="delay-1 fade-in-up">Achieve fluency faster with our AI-powered language learning platform. Personalized lessons, interactive flashcards, and conversational practice with our intelligent AI assistant.</p>
        <a href="/signup" className="btn btn-primary delay-2 fade-in-up">Start Learning For Free</a>
        </div>
        </div>
        </section>

        <section className="features section" id="features">
        <div className="container">
        <div className="section-header">
        <h2>Our Unique Features</h2>
        <p>LingvoPal combines the best language learning techniques with cutting-edge AI technology to create a personalized learning experience.</p>
        </div>
        <div className="features-grid">
        <div className="feature-card">
        <div className="feature-icon">🎮</div>
        <h3>Smart Flash Cards</h3>
        <p>Our interactive flash cards use sentences and images for better memorization. Advanced spaced repetition system ensures you remember vocabulary long-term.</p>
        </div>
        <div className="feature-card">
        <div className="feature-icon">🤖</div>
        <h3>AI Language Assistant</h3>
        <p>Practice conversations with our AI assistant that adapts to your level, provides instant feedback, and helps you improve your speaking and writing skills.</p>
        </div>
        <div className="feature-card">
        <div className="feature-icon">📊</div>
        <h3>Progress Tracking</h3>
        <p>Detailed statistics show your progress, most common mistakes, and learning patterns to help you optimize your study time.</p>
        </div>
        <div className="feature-card">
        <div className="feature-icon">🎯</div>
        <h3>Personalized Learning</h3>
        <p>Choose your focus areas (vocabulary, grammar, conversation) and get a customized learning path that adapts to your progress.</p>
        </div>
        <div className="feature-card">
        <div className="feature-icon">🌊</div>
        <h3>Language Immersion</h3>
        <p>Optional immersion mode where everything is in your target language to accelerate learning and improve comprehension.</p>
        </div>
        <div className="feature-card">
        <div className="feature-icon">📱</div>
        <h3>Learn Anywhere</h3>
        <p>Access LingvoPal on any device with reminders to help you maintain a consistent study schedule.</p>
        </div>
        </div>
        </div>
        </section>

        <section className="how-it-works section" id="how-it-works">
        <div className="container">
        <div className="section-header">
        <h2>How LingvoPal Works</h2>
        <p>Our platform makes language learning effective and enjoyable in just a few simple steps.</p>
        </div>
        <div className="steps">
        <div className="step">
        <div className="step-number">1</div>
        <h3>Sign Up</h3>
        <p>Create your account and select your target language and proficiency level.</p>
        </div>
        <div className="step">
        <div className="step-number">2</div>
        <h3>Customize</h3>
        <p>Set your learning goals and preferences to get a personalized learning path.</p>
        </div>
        <div className="step">
        <div className="step-number">3</div>
        <h3>Practice</h3>
        <p>Use flash cards, chat with AI, and complete exercises that adapt to your level.</p>
        </div>
        <div className="step">
        <div className="step-number">4</div>
        <h3>Progress</h3>
        <p>Track your improvement and adjust your learning strategy based on detailed analytics.</p>
        </div>
        </div>
        </div>
        </section>

        <section className="testimonials section" id="testimonials">
        <div className="container">
        <div className="section-header">
        <h2>What Our Users Say</h2>
        <p>Join thousands of satisfied learners who have improved their language skills with LingvoPal.</p>
        </div>
        <div className="testimonial-grid">
        <div className="testimonial-card">
        <div className="testimonial-text">LingvoPal's AI assistant made practicing Spanish conversations so much fun! It feels like talking to a patient tutor who never gets tired of correcting my mistakes.</div>
        <div className="testimonial-author">
        <div className="author-avatar">
        <img src="/img/avatar1.jpg" alt="Maria Lopez" />
        </div>
        <div className="author-info">
        <h4>Maria Lopez</h4>
        <p>Student, Spain</p>
        </div>
        </div>
        </div>
        <div className="testimonial-card">
        <div className="testimonial-text">The smart flashcards helped me remember French vocabulary faster than any other app I've tried. The progress tracking keeps me motivated!</div>
        <div className="testimonial-author">
        <div className="author-avatar">
        <img src="/img/avatar2.jpg" alt="James Carter" />
        </div>
        <div className="author-info">
        <h4>James Carter</h4>
        <p>Teacher, Canada</p>
        </div>
        </div>
        </div>
        <div className="testimonial-card">
        <div className="testimonial-text">I love the immersion mode! It pushed me to think in German, and now I feel much more confident with everyday conversations.</div>
        <div className="testimonial-author">
        <div className="author-avatar">
        <img src="/img/avatar3.jpg" alt="Anna Schmidt" />
        </div>
        <div className="author-info">
        <h4>Anna Schmidt</h4>
        <p>Engineer, Germany</p>
        </div>
        </div>
        </div>
        </div>
        </div>
        </section>

        <section className="cta section">
        <div className="container cta-container">
        <h2>Join LingvoPal Today</h2>
        <p>Start your language learning journey with a platform designed to make fluency achievable and enjoyable. Sign up now and experience the difference!</p>
        <a href="/signup" className="btn btn-light">Get Started For Free</a>
        </div>
        </section>

        <footer>
        <div className="container">
        <div className="footer-grid">
        <div className="footer-column">
        <h3>About LingvoPal</h3>
        <p>LingvoPal is an AI-powered language learning platform dedicated to helping you achieve fluency through personalized, engaging, and effective methods.</p>
        </div>
        <div className="footer-column">
        <h3>Quick Links</h3>
        <ul className="footer-links">
        <li><a href="#features">Features</a></li>
        <li><a href="#how-it-works">How It Works</a></li>
        <li><a href="#testimonials">Testimonials</a></li>
        <li><a href="/pricing">Pricing</a></li>
        </ul>
        </div>
        <div className="footer-column">
        <h3>Support</h3>
        <ul className="footer-links">
        <li><a href="/faq">FAQ</a></li>
        <li><a href="/contact">Contact Us</a></li>
        <li><a href="/terms">Terms of Service</a></li>
        <li><a href="/privacy">Privacy Policy</a></li>
        </ul>
        </div>
        <div className="footer-column">
        <h3>Connect</h3>
        <ul className="footer-links">
        <li><a href="/blog">Blog</a></li>
        <li><a href="/community">Community</a></li>
        <li><a href="/careers">Careers</a></li>
        </ul>
        </div>
        </div>
        <div className="footer-bottom">
        <div className="social-icons">
        <a href="https://facebook.com" className="social-icon" target="_blank" rel="noopener noreferrer">📘</a>
        <a href="https://twitter.com" className="social-icon" target="_blank" rel="noopener noreferrer">🐦</a>
        <a href="https://instagram.com" className="social-icon" target="_blank" rel="noopener noreferrer">📷</a>
        <a href="https://linkedin.com" className="social-icon" target="_blank" rel="noopener noreferrer">💼</a>
        </div>
        <p className="copyright">&copy; 2025 LingvoPal. All rights reserved.</p>
        </div>
        </div>
        </footer>
        </>
    );
};

export default Dashboard;
