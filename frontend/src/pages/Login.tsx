import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import './login-signup.module.css'
import Logo from '../components/Logo'
import LanguageSelector from '../components/LanguageSelector'
import SocialLogin from '../components/SocialLogin'
import { useAuth } from '../context/AuthContext'

const Login: React.FC = () => {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')

    const { login } = useAuth()
    const navigate = useNavigate()

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError('')

        try {
            await login(email, password)
            navigate('/dashboard')
        } catch (err) {
            setError('Failed to sign in. Please check your credentials.')
        }
    }

    return (
        <>
        <LanguageSelector />

        <div className="container">
        <Logo />

        <h2>Sign in to LingvoPal</h2>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
        <div className="form-group">
        <label htmlFor="email">Email</label>
        <input
        type="email"
        id="email"
        placeholder="Enter your email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
        />
        </div>

        <div className="form-group">
        <label htmlFor="password">Password</label>
        <input
        type="password"
        id="password"
        placeholder="Enter your password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        />
        </div>

        <div className="forgot-password">
        <Link to="/reset-password">Forgot password?</Link>
        </div>

        <button type="submit">Sign In</button>

        <p className="checkbox-group">
        By signing in, I agree to the LingvoPal's{' '}
        <Link to="/privacy-statement">Privacy Statement</Link> and{' '}
        <Link to="/terms-of-service">Terms of Service</Link>.
        </p>
        </form>

        <div className="or-divider">
        <span>Or sign up with</span>
        </div>

        <SocialLogin />

        <div className="signup-link">
        Don't have an account? <Link to="/signup">Sign up for free</Link>
        </div>
        </div>
        </>
    )
}

export default Login
