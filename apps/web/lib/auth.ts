import { UserRole } from "@/lib/types";

const TOKEN_KEY = "docflow_token";
const ROLE_KEY = "docflow_user_role";

export function getAuthToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(TOKEN_KEY);
}

export function getStoredRole(): UserRole | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(ROLE_KEY) as UserRole | null;
}

export function saveAuthSession(token: string, role: UserRole): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(TOKEN_KEY, token);
  window.localStorage.setItem(ROLE_KEY, role);
}

export function clearAuthSession(): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(ROLE_KEY);
}
