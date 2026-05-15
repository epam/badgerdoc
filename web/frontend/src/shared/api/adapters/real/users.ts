import type { UsersAdapter } from '../types'
import type { User } from '@/shared/types'
import { badgerDocClient } from '../../badgerdoc/client'

interface BadgerDocUserResponse {
  id: number
  username: string
  first_name: string
  last_name: string
  is_admin: boolean
}

export const realUsersAdapter: UsersAdapter = {
  async getCurrentUserData(): Promise<User> {
    const response = await badgerDocClient.get<BadgerDocUserResponse>('/user/me')

    return {
      id: response.data.id,
      name: `${response.data.first_name} ${response.data.last_name}`,
      role: response.data.is_admin ? 'admin' : 'reviewer',
      username: response.data.username,
    }
  },
}
