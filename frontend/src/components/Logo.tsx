import React from 'react'

const Logo: React.FC = () => {
    return (
        <div className="logo">
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
        <p>Your language learning companion</p>
        </div>
    )
}

export default Logo
