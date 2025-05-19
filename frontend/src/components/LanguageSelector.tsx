import React from 'react'

const LanguageSelector: React.FC = () => {
    return (
        <div className="language-selector">
        <select onChange={(e) => console.log('Language changed to:', e.target.value)}>
        <option value="en">English</option>
        <option value="pl">Polski</option>
        <option value="de">Deutsch</option>
        <option value="es">Español</option>
        <option value="ua">українська</option>
        </select>
        </div>
    )
}

export default LanguageSelector
