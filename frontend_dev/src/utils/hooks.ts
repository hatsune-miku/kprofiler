import { useRef, useState } from 'react'

export interface ImmutableRef<T> {
  readonly current: T
}

/**
 * 和 useState 等效，但是会同时维护一个 ref
 *
 * - state 给 UI 用，随着下次渲染才会更新
 * - ref 给逻辑用，它的值在 setState 后会立刻、同步地更新为最新值
 *
 * @returns [state, setState, ref]
 */
export function useStateSync<T>(
  initialValue: T | (() => T),
  useStateFunction = useState
): [T, (value: T | ((prev: T) => T)) => void, ImmutableRef<T>] {
  const [state, _setState] = useStateFunction(initialValue)
  const ref = useRef<T>(
    typeof initialValue === 'function'
      ? (initialValue as () => T)()
      : initialValue
  )

  const setState = (value: T | ((prev: T) => T)) => {
    const newValue =
      typeof value === 'function'
        ? (value as (prev: T) => T)(ref.current)
        : value
    ref.current = newValue
    _setState(value)
  }

  return [state, setState, ref as ImmutableRef<T>]
}
