// src/App.tsx
import { Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Dashboard from './pages/Dashboard'
import LandingPage from './pages/LandingPage'
import ResetPassword from './pages/ResetPassword'
import Settings from './pages/Settings'
import Chat from './pages/Chat'
import FlashCards from './pages/FlashCards'
import Sets from './pages/Sets'
import Support from './pages/Support'
import VerifyEmail from './pages/VerifyEmail' 
import PrivacyPolicy from './pages/PrivacyPolicy'
import TermsOfService from './pages/TermsOfService'

function App() {
  return (
    <AuthProvider>
    <Routes>
    <Route path="/" element={<LandingPage />} />
    <Route path="/login" element={<Login />} />
    <Route path="/signup" element={<Signup />} />
    <Route path="/dashboard" element={<Dashboard />} />
    <Route path="/reset-password" element={<ResetPassword />} />
    <Route path="/settings" element={<Settings />} />
    <Route path="/chat" element={<Chat />} />
    <Route path="/flashcards" element={<FlashCards />} />
    <Route path="/sets" element={<Sets />} />
    <Route path="/support" element={<Support />} />
    <Route path="/verify-email" element={<VerifyEmail />} />
    <Route path="/privacy-policy" element={<PrivacyPolicy />} />
    <Route path="/terms" element={<TermsOfService />} />
    </Routes>
    </AuthProvider>
  )
}

export default App
