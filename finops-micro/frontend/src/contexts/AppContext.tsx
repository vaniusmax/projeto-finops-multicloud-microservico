"use client";

import { createContext, useContext, useEffect, useState } from "react";

import type { CompareMode, DashboardFilters } from "@/lib/query/search-params";

type SavedView = {
  id: string;
  name: string;
  filters: DashboardFilters;
};

type AppContextValue = {
  filters: DashboardFilters;
  updateFilters: (patch: Partial<DashboardFilters>) => void;
  compareMode: CompareMode;
  setCompareMode: (mode: CompareMode) => void;
  refreshTick: number;
  triggerRefresh: () => void;
  isFilterDrawerOpen: boolean;
  setFilterDrawerOpen: (open: boolean) => void;
  isSidebarCollapsed: boolean;
  setSidebarCollapsed: (collapsed: boolean) => void;
  savedViews: SavedView[];
  saveCurrentView: (name: string) => void;
  applySavedView: (id: string) => void;
  deleteSavedView: (id: string) => void;
};

const AppContext = createContext<AppContextValue | null>(null);

const STORAGE_KEYS = {
  compareMode: "finops:compare-mode",
  sidebarCollapsed: "finops:sidebar-collapsed",
  savedViews: "finops:saved-views",
};

type AppProviderProps = {
  children: React.ReactNode;
  filters: DashboardFilters;
  onUpdateFilters: (patch: Partial<DashboardFilters>) => void;
};

export function AppProvider({ children, filters, onUpdateFilters }: AppProviderProps) {
  const [compareMode, setCompareModeState] = useState<CompareMode>("off");
  const [refreshTick, setRefreshTick] = useState(0);
  const [isFilterDrawerOpen, setFilterDrawerOpen] = useState(false);
  const [isSidebarCollapsed, setSidebarCollapsedState] = useState(false);
  const [savedViews, setSavedViews] = useState<SavedView[]>([]);

  useEffect(() => {
    const storedCompareMode = window.localStorage.getItem(STORAGE_KEYS.compareMode) as CompareMode | null;
    const storedSidebar = window.localStorage.getItem(STORAGE_KEYS.sidebarCollapsed);
    const storedViews = window.localStorage.getItem(STORAGE_KEYS.savedViews);

    if (storedCompareMode === "off" || storedCompareMode === "previous-period") {
      setCompareModeState(storedCompareMode);
    }
    if (storedSidebar === "true") {
      setSidebarCollapsedState(true);
    }
    if (storedViews) {
      try {
        const parsed = JSON.parse(storedViews) as SavedView[];
        if (Array.isArray(parsed)) {
          setSavedViews(parsed);
        }
      } catch {
        window.localStorage.removeItem(STORAGE_KEYS.savedViews);
      }
    }
  }, []);

  function setCompareMode(mode: CompareMode) {
    setCompareModeState(mode);
    window.localStorage.setItem(STORAGE_KEYS.compareMode, mode);
  }

  function setSidebarCollapsed(collapsed: boolean) {
    setSidebarCollapsedState(collapsed);
    window.localStorage.setItem(STORAGE_KEYS.sidebarCollapsed, String(collapsed));
  }

  function triggerRefresh() {
    setRefreshTick((value) => value + 1);
  }

  function persistSavedViews(next: SavedView[]) {
    setSavedViews(next);
    window.localStorage.setItem(STORAGE_KEYS.savedViews, JSON.stringify(next));
  }

  function saveCurrentView(name: string) {
    const trimmed = name.trim();
    if (!trimmed) return;
    const entry: SavedView = {
      id: `${Date.now()}`,
      name: trimmed,
      filters,
    };
    persistSavedViews([entry, ...savedViews].slice(0, 8));
  }

  function applySavedView(id: string) {
    const match = savedViews.find((item) => item.id === id);
    if (!match) return;
    onUpdateFilters(match.filters);
  }

  function deleteSavedView(id: string) {
    persistSavedViews(savedViews.filter((item) => item.id !== id));
  }

  const value: AppContextValue = {
    filters,
    updateFilters: onUpdateFilters,
    compareMode,
    setCompareMode,
    refreshTick,
    triggerRefresh,
    isFilterDrawerOpen,
    setFilterDrawerOpen,
    isSidebarCollapsed,
    setSidebarCollapsed,
    savedViews,
    saveCurrentView,
    applySavedView,
    deleteSavedView,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppContext() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useAppContext must be used within AppProvider");
  }
  return context;
}
