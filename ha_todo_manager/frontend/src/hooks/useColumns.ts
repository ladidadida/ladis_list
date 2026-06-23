import { useQuery } from '@tanstack/react-query'
import { fetchColumns } from '../api/client'

export const COLUMNS_KEY = (boardId: string) => ['columns', boardId] as const

export function useColumns(boardId: string) {
  return useQuery({
    queryKey: COLUMNS_KEY(boardId),
    queryFn: () => fetchColumns(boardId),
    enabled: Boolean(boardId),
  })
}
