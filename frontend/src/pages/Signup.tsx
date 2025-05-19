import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import '../styles/login-signup.css'
import Logo from '../components/Logo'
import LanguageSelector from '../components/LanguageSelector'
import Step1Account from './SignupSteps/Step1Account'
import Step2Language from './SignupSteps/Step2Language'
import Step3Goals from './SignupSteps/Step3Goals'
import SignupSuccess from './SignupSteps/SignupSuccess'
import { useAuth } from '../context/AuthContext'

// Define the step names
const stepNames = ['Account Setup', 'Language Selection', 'Learning Goals']

const Signup: React.FC = () => {
    const [currentStep, setCurrentStep] = useState(1)
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        password: '',
        agreeToTerms: false,
        receiveNewsletter: false,
        nativeLanguage: '',
        learningLanguage: '',
        proficiencyLevel: '',
        learningGoal: '',
        dailyTime: 15
    })

    const { signup } = useAuth()
    const navigate = useNavigate()

    // Calculate progress percentage
    const progressPercentage = (currentStep / 3) * 100

    // Handle form data changes
    const updateFormData = (data: Partial<typeof formData>) => {
        setFormData(prev => ({ ...prev, ...data }))
    }

    // Navigate to next step
    const nextStep = () => {
        setCurrentStep(prev => Math.min(prev + 1, 4))
    }

    // Navigate to previous step
    const prevStep = () => {
        setCurrentStep(prev => Math.max(prev - 1, 1))
    }

    // Handle final submission
    const handleSubmit = async () => {
        try {
            await signup({
                name: formData.name,
                email: formData.email,
                password: formData.password,
                nativeLanguage: formData.nativeLanguage,
                learningLanguage: formData.learningLanguage
            })
            nextStep() // Show success page
        } catch (err) {
            console.error('Signup failed:', err)
            // Handle error
        }
    }

    // Start learning after successful signup
    const startLearning = () => {
        navigate('/dashboard')
    }

    return (
        <>
        <LanguageSelector />

        <div className="container">
        <div className="signup-form">
        <Logo />

        <div className="progress-bar">
        <div
        className="progress-filled"
        style={{ width: `${progressPercentage}%` }}
        ></div>
        </div>

        <div className="step-info">
        <div className="step-name">
        {currentStep <= 3 ? stepNames[currentStep - 1] : "You're In!"}
        </div>
        <div className="steps-count">
        Step <span>{Math.min(currentStep, 3)}</span> of 3
        </div>
        </div>

        {/* Render the current step */}
        {currentStep === 1 && (
            <Step1Account
            formData={formData}
            updateFormData={updateFormData}
            onNext={nextStep}
            />
        )}

        {currentStep === 2 && (
            <Step2Language
            formData={formData}
            updateFormData={updateFormData}
            onNext={nextStep}
            onPrev={prevStep}
            />
        )}

        {currentStep === 3 && (
            <Step3Goals
            formData={formData}
            updateFormData={updateFormData}
            onPrev={prevStep}
            onSubmit={handleSubmit}
            />
        )}

        {currentStep === 4 && <SignupSuccess onStartLearning={startLearning} />}
        </div>
        </div>
        </>
    )
}

export default Signup
