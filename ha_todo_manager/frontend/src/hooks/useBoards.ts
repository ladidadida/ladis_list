import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createBoard,
  deleteBoard,
  fetchBoards,
  updateBoard,
  type BoardCreate,
  type BoardUpdate,
} from '../api/client'

export const BOARDS_KEY = ['boards'] as const

export function useBoards() {
  return useQuery({ queryKey: BOARDS_KEY, queryFn: fetchBoards })
}

export function useCreateBoard() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: BoardCreate) => createBoard(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: BOARDS_KEY }),
  })
}

export function useUpdateBoard() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: BoardUpdate }) => updateBoard(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: BOARDS_KEY }),
  })
}

export function useDeleteBoard() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteBoard(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: BOARDS_KEY }),
  })
}
