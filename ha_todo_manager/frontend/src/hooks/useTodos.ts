import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  completeTodo,
  createTodo,
  deleteTodo,
  fetchTodos,
  updateTodo,
  type TodoCreate,
  type TodoUpdate,
} from '../api/client'

const TODOS_BASE_KEY = ['todos'] as const
export const TODOS_KEY = (boardId: string, mine?: boolean) =>
  mine ? ([...TODOS_BASE_KEY, boardId, { mine: true }] as const) : ([...TODOS_BASE_KEY, boardId] as const)

export function useTodos(boardId: string, mine?: boolean) {
  return useQuery({
    queryKey: TODOS_KEY(boardId, mine),
    queryFn: () => fetchTodos(boardId, mine),
    enabled: Boolean(boardId),
  })
}

export function useCreateTodo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: TodoCreate) => createTodo(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: TODOS_BASE_KEY }),
  })
}

export function useUpdateTodo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TodoUpdate }) => updateTodo(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: TODOS_BASE_KEY }),
  })
}

export function useCompleteTodo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => completeTodo(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: TODOS_BASE_KEY }),
  })
}

export function useDeleteTodo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteTodo(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: TODOS_BASE_KEY }),
  })
}

// Batches multiple position/column updates from a single Kanban drag-end into one
// mutation, so the todos query is only invalidated once.
export function useMoveTodo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (updates: { id: string; data: TodoUpdate }[]) => {
      await Promise.all(updates.map(({ id, data }) => updateTodo(id, data)))
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: TODOS_BASE_KEY }),
  })
}
