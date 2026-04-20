import type { User } from '@/shared/types'

export interface AuthAdapter {
  getToken(): Promise<string | null>
  refreshToken(): Promise<string>
  login(credentials?: unknown): Promise<void>
  logout(): Promise<void>
  isAuthenticated(): boolean
  getUser(): User | null
}

export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
}
