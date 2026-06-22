import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createPerson, deletePerson, fetchPersons, syncPersons, type PersonCreate } from '../api/client'

export const PERSONS_KEY = ['persons'] as const

export function usePersons() {
  return useQuery({ queryKey: PERSONS_KEY, queryFn: fetchPersons })
}

export function useSyncPersons() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: syncPersons,
    onSuccess: () => qc.invalidateQueries({ queryKey: PERSONS_KEY }),
  })
}

export function useCreatePerson() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: PersonCreate) => createPerson(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: PERSONS_KEY }),
  })
}

export function useDeletePerson() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deletePerson(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: PERSONS_KEY }),
  })
}
