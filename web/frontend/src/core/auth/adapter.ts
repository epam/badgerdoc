import type { User } from '@/shared/types'
import type { AuthAdapter } from './types'
import { getCsrfToken } from '@/helpers/get-csrf-token'

class MockAuthAdapter implements AuthAdapter {
  private token: string | null = getCsrfToken()
  private user: User | null = null

  async getToken(): Promise<string | null> {
    return this.token
  }

  async refreshToken(): Promise<string> {
    this.token = 'refreshed-mock-token'
    return this.token
  }

  async login(_credentials?: unknown): Promise<void> {
    this.token = null
    this.user = null

    window.location.href = window.location.origin + '/admin/login/?next=/ui/documents/'
  }

  async logout(): Promise<void> {
    this.token = null
    this.user = null
  }

  isAuthenticated(): boolean {
    return this.token !== null
  }

  getUser(): User | null {
    return this.user
  }
}

export const authAdapter: AuthAdapter = new MockAuthAdapter()
