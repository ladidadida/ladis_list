import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createTag, deleteTag, fetchTags, type TagCreate } from '../api/client'

export const TAGS_KEY = ['tags'] as const

export function useTags() {
  return useQuery({ queryKey: TAGS_KEY, queryFn: fetchTags })
}

export function useCreateTag() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: TagCreate) => createTag(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: TAGS_KEY }),
  })
}

export function useDeleteTag() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteTag(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: TAGS_KEY }),
  })
}
