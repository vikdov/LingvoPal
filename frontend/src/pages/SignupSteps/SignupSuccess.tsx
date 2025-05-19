import React from 'react'

interface SignupSuccessProps {
    onStartLearning: () => void
}

const SignupSuccess: React.FC<SignupSuccessProps> = ({ onStartLearning }) => {
    return (
        <div className="form-step active">
        <div className="congratulations">
        <h3>Congratulations!</h3>
        <p>Your LingvoPal account has been created successfully.</p>
        <p>We've tailored a learning plan based on your preferences.</p>
        <button type="button" onClick={onStartLearning}>
        Start Learning Now
        </button>
        </div>
        </div>
    )
}

export default SignupSuccess
