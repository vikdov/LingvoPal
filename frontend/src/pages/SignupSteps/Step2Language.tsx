import React, { useState } from 'react'

interface Step2Props {
    formData: {
        nativeLanguage: string
        learningLanguage: string
        proficiencyLevel: string
    }
    updateFormData: (data: Partial<Step2Props['formData']>) => void
    onNext: () => void
    onPrev: () => void
}

const Step2Language: React.FC<Step2Props> = ({
    formData,
        updateFormData,
        onNext,
        onPrev
}) => {
    const [errors, setErrors] = useState<Record<string, string>>({})

    const validateStep = () => {
        const newErrors: Record<string, string> = {}

        if (!formData.nativeLanguage) newErrors.nativeLanguage = 'Please select your native language'
            if (!formData.learningLanguage) newErrors.learningLanguage = 'Please select a language to learn'

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
        <h2>Choose your languages</h2>

        <div className="form-group">
        <label htmlFor="native-language">Native Language</label>
        <select
        id="native-language"
        value={formData.nativeLanguage}
        onChange={(e) => updateFormData({ nativeLanguage: e.target.value })}
        required
        >
        <option value="" disabled>Select your native language</option>
        <option value="pl">Polish</option>
        <option value="en">English</option>
        <option value="de">German</option>
        <option value="es">Spanish</option>
        </select>
        {errors.nativeLanguage && <div className="error-message">{errors.nativeLanguage}</div>}
        </div>

        <div className="form-group">
        <label htmlFor="learning-language">Language to Learn</label>
        <select
        id="learning-language"
        value={formData.learningLanguage}
        onChange={(e) => updateFormData({ learningLanguage: e.target.value })}
        required
        >
        <option value="" disabled>Select language to learn</option>
        <option value="en">English</option>
        <option value="de">German</option>
        <option value="es">Spanish</option>
        </select>
        {errors.learningLanguage && <div className="error-message">{errors.learningLanguage}</div>}
        </div>

        <div className="form-group">
        <label htmlFor="proficiency">Current Proficiency Level</label>
        <select
        id="proficiency"
        value={formData.proficiencyLevel}
        onChange={(e) => updateFormData({ proficiencyLevel: e.target.value })}
        >
        <option value="" disabled>Select your current level</option>
        <option value="not-specified">I don't know / Take a placement test later</option>
        <option value="beginner">Beginner (A1)</option>
        <option value="elementary">Elementary (A2)</option>
        <option value="intermediate">Intermediate (B1)</option>
        <option value="upper-intermediate">Upper Intermediate (B2)</option>
        <option value="advanced">Advanced (C1)</option>
        <option value="proficient">Proficient (C2)</option>
        </select>
        </div>

        <div className="button-group">
        <button type="button" className="btn-prev" onClick={onPrev}>
        Back
        </button>
        <button type="button" className="btn-next" onClick={handleNext}>
        Continue
        </button>
        </div>
        </div>
    )
}

export default Step2Language
