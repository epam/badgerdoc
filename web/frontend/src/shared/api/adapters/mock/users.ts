import type { UsersAdapter } from '../types'

export const mockUsersAdapter: UsersAdapter = {
  async getCurrentUserData() {
    return {
      id: 1,
      name: 'Mock Admin',
      role: 'admin',
      username: 'mock-admin',
    }
  },
}
