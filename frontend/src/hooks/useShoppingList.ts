import {
  createCategory,
  createItem,
  createList,
  deleteCategory,
  deleteCheckedItems,
  deleteItem,
  deleteList,
  fetchCategories,
  fetchItems,
  fetchLists,
  reorderCategories,
  updateItem,
  type CategoryCreate,
  type CategoryReorderItem,
  type ItemCreate,
  type ItemUpdate,
  type ShoppingListCreate,
} from '../api/client'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

export const LISTS_KEY = ['lists'] as const
export const CATEGORIES_KEY = ['categories'] as const
export const ITEMS_KEY = (listId?: number): readonly (string | number)[] =>
  listId !== undefined ? ['items', listId] : ['items']

// ─── Shopping Lists ───────────────────────────────────────────────────────────

export function useLists() {
  return useQuery({ queryKey: LISTS_KEY, queryFn: fetchLists })
}

export function useCreateList() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: ShoppingListCreate) => createList(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: LISTS_KEY }),
  })
}

export function useDeleteList() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deleteList(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: LISTS_KEY })
      qc.invalidateQueries({ queryKey: ['items'] })
    },
  })
}

// ─── Categories ───────────────────────────────────────────────────────────────

export function useCategories() {
  return useQuery({ queryKey: CATEGORIES_KEY, queryFn: fetchCategories })
}

export function useCreateCategory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: CategoryCreate) => createCategory(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: CATEGORIES_KEY }),
  })
}

export function useDeleteCategory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deleteCategory(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: CATEGORIES_KEY })
      qc.invalidateQueries({ queryKey: ['items'] })
    },
  })
}

export function useReorderCategories() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (items: CategoryReorderItem[]) => reorderCategories(items),
    onMutate: async (items) => {
      await qc.cancelQueries({ queryKey: CATEGORIES_KEY })
      const previous = qc.getQueryData(CATEGORIES_KEY)
      qc.setQueryData(CATEGORIES_KEY, (old: CategoryReorderItem[] | undefined) => {
        if (!old) return old
        const orderMap = new Map(items.map((i) => [i.id, i.sort_order]))
        return [...old]
          .map((c) => ({ ...c, sort_order: orderMap.get(c.id) ?? (c as { sort_order: number }).sort_order }))
          .sort((a, b) => (a as { sort_order: number }).sort_order - (b as { sort_order: number }).sort_order)
      })
      return { previous }
    },
    onError: (_err, _items, ctx) => {
      if (ctx?.previous !== undefined) qc.setQueryData(CATEGORIES_KEY, ctx.previous)
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: CATEGORIES_KEY })
      qc.invalidateQueries({ queryKey: ['items'] })
    },
  })
}

// ─── Items ────────────────────────────────────────────────────────────────────

export function useItems(listId?: number) {
  return useQuery({
    queryKey: ITEMS_KEY(listId),
    queryFn: () => fetchItems(listId),
  })
}

export function useCreateItem(listId?: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: ItemCreate) => createItem({ ...data, list_id: listId ?? null }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ITEMS_KEY(listId) }),
  })
}

export function useToggleItem(listId?: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, checked }: { id: number; checked: boolean }) =>
      updateItem(id, { checked }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ITEMS_KEY(listId) }),
  })
}

export function useUpdateItem(listId?: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ItemUpdate }) =>
      updateItem(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ITEMS_KEY(listId) }),
  })
}

export function useDeleteItem(listId?: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deleteItem(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ITEMS_KEY(listId) }),
  })
}

export function useDeleteCheckedItems(listId?: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => deleteCheckedItems(listId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ITEMS_KEY(listId) }),
  })
}
