import { useMutation, useQuery } from '@tanstack/react-query'
import apiClient from '@/api/client'
import { useAuthStore } from '@/stores/authStore'

export function useLogin() {
  const { login } = useAuthStore()
  return useMutation({
    mutationFn: ({ username, password }: { username: string; password: string }) =>
      login(username, password),
  })
}

export function useRegister() {
  const { register } = useAuthStore()
  return useMutation({
    mutationFn: ({ username, email, password }: { username: string; email: string; password: string }) =>
      register(username, email, password),
  })
}

export function useLogout() {
  const { logout } = useAuthStore()
  return useMutation({
    mutationFn: () => Promise.resolve(logout()),
  })
}

export function useCurrentUser() {
  const { checkAuth, user, isAuthenticated, isLoading } = useAuthStore()

  const query = useQuery({
    queryKey: ['currentUser'],
    queryFn: () => checkAuth(),
    enabled: false,
  })

  return {
    user,
    isAuthenticated,
    isLoading: isLoading || query.isLoading,
    refetch: query.refetch,
  }
}

export function useUpdateProfile() {
  const { updateProfile } = useAuthStore()
  return useMutation({
    mutationFn: (data: { username?: string; email?: string }) => updateProfile(data),
  })
}

export function useUpdatePassword() {
  const { updatePassword } = useAuthStore()
  return useMutation({
    mutationFn: ({ currentPassword, newPassword }: { currentPassword: string; newPassword: string }) =>
      updatePassword(currentPassword, newPassword),
  })
}
