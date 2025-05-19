import React from 'react'

const SocialLogin: React.FC = () => {
    return (
        <div className="social-login">
        <div className="social-btn">
        <a href="https://www.google.com/">
        <img className="social-img" src="/src/assets/google.png" alt="Google login method" />
        </a>
        </div>
        <div className="social-btn">
        <a href="https://www.facebook.com/">
        <img className="social-img" src="/src/assets/facebook.png" alt="Facebook login method" />
        </a>
        </div>
        <div className="social-btn">
        <a href="https://www.apple.com/">
        <img className="social-img" src="/src/assets/appleid.png" alt="Apple ID login method" />
        </a>
        </div>
        </div>
    )
}

export default SocialLogin
