import React, { createContext, useState, useContext, ReactNode } from 'react'

// Define types
interface User {
    id: string
    name: string
    email: string
    nativeLanguage?: string
    learningLanguage?: string
}

interface AuthContextType {
    user: User | null
    login: (email: string, password: string) => Promise<void>
    signup: (userData: Partial<User> & { password: string }) => Promise<void>
    logout: () => void
    isAuthenticated: boolean
}

// Create the context
const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Provider component
export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null)

    const login = async (email: string, password: string) => {
        // Here you would normally call an API
        console.log('Login with:', email, password)

        // Simulate successful login
        setUser({
            id: '1',
            name: 'Test User',
            email: email
        })
    }

    const signup = async (userData: Partial<User> & { password: string }) => {
        // Here you would normally call an API
        console.log('Signup with:', userData)

        // Simulate successful registration
        if (userData.email && userData.name) {
            setUser({
                id: '1',
                name: userData.name,
                email: userData.email,
                nativeLanguage: userData.nativeLanguage,
                learningLanguage: userData.learningLanguage
            })
        }
    }

    const logout = () => {
        setUser(null)
    }

    const value = {
        user,
        login,
        signup,
        logout,
        isAuthenticated: !!user
    }

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// Custom hook to use the auth context
export const useAuth = () => {
    const context = useContext(AuthContext)
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider')
    }
    return context
}
