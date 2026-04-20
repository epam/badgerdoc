import { useCallback } from 'react'
import { create } from 'zustand'
import { authAdapter } from './adapter'
import type { AuthState } from './types'
import type { User } from '@/shared/types'
import { badgerDocService } from '@/shared/api/badgerdoc'

interface AuthStore extends AuthState {
  setUser: (user: User | null) => void
  setLoading: (isLoading: boolean) => void
}

const useAuthStore = create<AuthStore>((set) => ({
  user: authAdapter.getUser(),
  isAuthenticated: authAdapter.isAuthenticated(),
  isLoading: false,
  setUser: (user) => set({ user, isAuthenticated: user !== null }),
  setLoading: (isLoading) => set({ isLoading }),
}))

export function useAuth() {
  const { user, isAuthenticated, isLoading, setUser, setLoading } = useAuthStore()

  const login = useCallback(
    async (credentials?: unknown) => {
      setLoading(true)
      try {
        await authAdapter.login(credentials)
        setUser(authAdapter.getUser())
      } finally {
        setLoading(false)
      }
    },
    [setUser, setLoading]
  )

  const logout = useCallback(async () => {
    setLoading(true)
    try {
      await authAdapter.logout()
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [setUser, setLoading])

  const getCurrentUserData = useCallback(async () => {
    setLoading(true)
    try {
      const userData = await badgerDocService.getCurrentUserData()
      setUser(userData)
    } finally {
      setLoading(false)
    }
  }, [setUser, setLoading])

  return {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    getCurrentUserData,
  }
}
