"use client";

import { useState, useCallback } from "react";

// Boolean Toggle Hook
export function useToggle(initial = false): [boolean, () => void] {
  const [value, setValue] = useState(initial);
  const toggle = useCallback(() => setValue((prev) => !prev), []);
  return [value, toggle];
}
