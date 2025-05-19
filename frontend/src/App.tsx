// src/App.tsx
import { Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Dashboard from './pages/Dashboard'
import Landing from './pages/Landing'

function App() {
  return (
    <AuthProvider>
    <Routes>
    <Route path="/" element={<Landing />} />
    <Route path="/login" element={<Login />} />
    <Route path="/signup" element={<Signup />} />
    <Route path="/dashboard" element={<Dashboard />} />
    </Routes>
    </AuthProvider>
  )
}

export default App
