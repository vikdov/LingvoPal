import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import SocialLogin from '../../components/SocialLogin'

interface Step1Props {
    formData: {
        name: string
        email: string
        password: string
        agreeToTerms: boolean
        receiveNewsletter: boolean
    }
    updateFormData: (data: Partial<Step1Props['formData']>) => void
    onNext: () => void
}

const Step1Account: React.FC<Step1Props> = ({ formData, updateFormData, onNext }) => {
    const [errors, setErrors] = useState<Record<string, string>>({})

    const validateStep = () => {
        const newErrors: Record<string, string> = {}

        if (!formData.name) newErrors.name = 'Name is required'
            if (!formData.email) newErrors.email = 'Email is required'
                if (!formData.password) newErrors.password = 'Password is required'
                    else if (formData.password.length < 8) newErrors.password = 'Password must be at least 8 characters'
                        if (!formData.agreeToTerms) newErrors.terms = 'You must accept the terms and conditions'

                            setErrors(newErrors)
                            return Object.keys(newErrors).length === 0
    }

    const handleNext = () => {
        if (validateStep()) {
            onNext()
        }
    }

    return (
        <div className="form-step active">
        <h2>Create your account</h2>

        <div className="form-group">
        <label htmlFor="name">Full Name</label>
        <input
        type="text"
        id="name"
        placeholder="Enter your full name"
        value={formData.name}
        onChange={(e) => updateFormData({ name: e.target.value })}
        required
        />
        {errors.name && <div className="error-message">{errors.name}</div>}
        </div>

        <div className="form-group">
        <label htmlFor="email">Email</label>
        <input
        type="email"
        id="email"
        placeholder="Enter your email"
        value={formData.email}
        onChange={(e) => updateFormData({ email: e.target.value })}
        required
        />
        {errors.email && <div className="error-message">{errors.email}</div>}
        </div>

        <div className="form-group">
        <label htmlFor="password">Password</label>
        <input
        type="password"
        id="password"
        placeholder="Create a password (8+ characters)"
        value={formData.password}
        onChange={(e) => updateFormData({ password: e.target.value })}
        required
        />
        {errors.password && <div className="error-message">{errors.password}</div>}
        </div>

        <div className="checkbox-group">
        <div className="checkbox-item">
        <input
        type="checkbox"
        id="terms"
        checked={formData.agreeToTerms}
        onChange={(e) => updateFormData({ agreeToTerms: e.target.checked })}
        required
        />
        <label htmlFor="terms" className="checkbox">
        I agree to the <Link to="/terms-of-service">Terms of Service</Link> and{' '}
        <Link to="/privacy-policy">Privacy Policy</Link>
        </label>
        {errors.terms && <div className="error-message">{errors.terms}</div>}
        </div>

        <div className="checkbox-item">
        <input
        type="checkbox"
        id="newsletter"
        checked={formData.receiveNewsletter}
        onChange={(e) => updateFormData({ receiveNewsletter: e.target.checked })}
        />
        <label htmlFor="newsletter" className="checkbox">
        Send me learning tips and updates
        </label>
        </div>
        </div>

        <button type="button" className="btn-next" onClick={handleNext}>
        Continue
        </button>

        <div className="or-divider">
        <span>OR</span>
        </div>

        <SocialLogin />

        <div className="login-link">
        Already have an account? <Link to="/login">Log in</Link>
        </div>
        </div>
    )
}

export default Step1Account
