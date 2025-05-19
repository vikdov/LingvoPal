import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import LanguageSelector from '../components/LanguageSelector'

const Dashboard: React.FC = () => {
    const { user, logout } = useAuth()
    const navigate = useNavigate()

    const handleLogout = () => {
        logout()
        navigate('/login')
    }

    return (
        <div>
        <LanguageSelector />

        <header className="dashboard-header">
        <div className="container">
        <div className="logo-small">
        <h1>
        Lingv
        <span>
        <img
        className="globe"
        src="/src/assets/earth-americas-solid.svg"
        alt="Globe icon"
        />
        </span>
        <span>Pal</span>
        </h1>
        </div>

        <div className="user-controls">
        <div className="user-info">
        <span>Welcome, {user?.name}</span>
        </div>
        <button className="logout-btn" onClick={handleLogout}>
        Logout
        </button>
        </div>
        </div>
        </header>

        <main className="dashboard-content">
        <div className="container">
        <h2>Your Learning Dashboard</h2>

        <div className="dashboard-welcome">
        <h3>Welcome to LingvoPal!</h3>
        <p>Your personalized language learning journey starts here.</p>
        </div>

        <div className="language-info">
        <h4>You are learning: {user?.learningLanguage === 'en' ? 'English' :
            user?.learningLanguage === 'de' ? 'German' :
            user?.learningLanguage === 'es' ? 'Spanish' :
            'Your selected language'}</h4>
            </div>

            <div className="learning-modules">
            <h3>Today's Learning Modules</h3>

            <div className="module-card">
            <h4>Vocabulary Builder</h4>
            <p>Learn 10 new words today</p>
            <button>Start Learning</button>
            </div>

            <div className="module-card">
            <h4>Grammar Practice</h4>
            <p>Present tense practice</p>
            <button>Start Exercise</button>
            </div>

            <div className="module-card">
            <h4>Listening Comprehension</h4>
            <p>Daily conversation practice</p>
            <button>Start Listening</button>
            </div>
            </div>

            <div className="progress-section">
            <h3>Your Progress</h3>
            <p>You're just getting started! Complete your first lesson to see your progress.</p>
            </div>
            </div>
            </main>
            </div>
    )
}

export default Dashboard
