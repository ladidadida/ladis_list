import { useQuery } from '@tanstack/react-query'
import { fetchColumns } from '../api/client'

export const COLUMNS_KEY = ['columns'] as const

export function useColumns() {
  return useQuery({ queryKey: COLUMNS_KEY, queryFn: fetchColumns })
}
