import React, { useState } from 'react'

interface Step3Props {
    formData: {
        learningGoal: string
        dailyTime: number
    }
    updateFormData: (data: Partial<Step3Props['formData']>) => void
    onPrev: () => void
    onSubmit: () => void
}

const Step3Goals: React.FC<Step3Props> = ({
    formData,
        updateFormData,
        onPrev,
        onSubmit
}) => {
    const [errors, setErrors] = useState<Record<string, string>>({})

    const goalOptions = [
        { id: 'travel', name: 'Travel', description: 'Learn essential phrases and cultural insights for your trips' },
        { id: 'business', name: 'Work & Business', description: 'Focus on professional vocabulary and communication skills' },
        { id: 'academic', name: 'Academic', description: 'Prepare for exams or enhance your academic language skills' },
        { id: 'cultural', name: 'Cultural Interest', description: 'Explore literature, films, music, and cultural nuances' },
        { id: 'other', name: 'Other', description: "Don't specify/specify after" },
    ]

    const validateStep = () => {
        const newErrors: Record<string, string> = {}

        if (!formData.learningGoal) {
            newErrors.goal = 'Please select a learning goal'
        }

        setErrors(newErrors)
        return Object.keys(newErrors).length === 0
    }

    const handleSubmit = () => {
        if (validateStep()) {
            onSubmit()
        }
    }

    const handleGoalSelect = (goalId: string) => {
        updateFormData({ learningGoal: goalId })
    }

    return (
        <div className="form-step active">
        <h2>Set your learning goals</h2>

        <p>What's your primary reason for learning this language?</p>

        {errors.goal && <div className="error-message">{errors.goal}</div>}

        {goalOptions.map(goal => (
            <div
            key={goal.id}
            className={`goal-item ${formData.learningGoal === goal.id ? 'selected' : ''}`}
            onClick={() => handleGoalSelect(goal.id)}
            >
            <h4>{goal.name}</h4>
            <p>{goal.description}</p>
            </div>
        ))}

        <div className="time-commitment">
        <label htmlFor="time-slider">How much time can you commit daily?</label>
        <input
        type="range"
        id="time-slider"
        min="5"
        max="60"
        step="5"
        value={formData.dailyTime}
        onChange={(e) => updateFormData({ dailyTime: parseInt(e.target.value) })}
        className="time-slider"
        />
        <p id="time-value">{formData.dailyTime} minutes per day</p>
        </div>

        <div className="button-group">
        <button type="button" className="btn-prev" onClick={onPrev}>
        Back
        </button>
        <button type="button" className="btn-next" onClick={handleSubmit}>
        Create Account & Start Learning
        </button>
        </div>
        </div>
    )
}

export default Step3Goals
