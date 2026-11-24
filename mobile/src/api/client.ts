import * as SecureStore from 'expo-secure-store';

export const API_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';

const ACCESS = 'stryde.access';
const REFRESH = 'stryde.refresh';

export class ApiError extends Error {
  constructor(
    public status: number,
    public body: unknown,
  ) {
    super(typeof body === 'object' && body && 'detail' in body ? String((body as { detail: unknown }).detail) : `HTTP ${status}`);
  }
}

let onAuthChange: ((signedIn: boolean) => void) | null = null;
export function setAuthChangeHandler(fn: (signedIn: boolean) => void) {
  onAuthChange = fn;
}

export async function getAccessToken() {
  return SecureStore.getItemAsync(ACCESS);
}

export async function saveTokens(access: string, refresh?: string) {
  await SecureStore.setItemAsync(ACCESS, access);
  if (refresh) await SecureStore.setItemAsync(REFRESH, refresh);
}

export async function signOut() {
  await SecureStore.deleteItemAsync(ACCESS);
  await SecureStore.deleteItemAsync(REFRESH);
  onAuthChange?.(false);
}

async function refreshAccess(): Promise<string | null> {
  const refresh = await SecureStore.getItemAsync(REFRESH);
  if (!refresh) return null;
  const res = await fetch(`${API_URL}/api/auth/token/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  });
  if (!res.ok) return null;
  const data = (await res.json()) as { access: string; refresh?: string };
  await saveTokens(data.access, data.refresh);
  return data.access;
}

type Options = { method?: string; body?: unknown; form?: FormData; auth?: boolean };

export async function api<T = unknown>(path: string, opts: Options = {}): Promise<T> {
  const { method = opts.body || opts.form ? 'POST' : 'GET', body, form, auth = true } = opts;
  const send = async (token: string | null) => {
    const headers: Record<string, string> = { Accept: 'application/json' };
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    if (auth && token) headers.Authorization = `Bearer ${token}`;
    return fetch(`${API_URL}${path}`, { method, headers, body: form ?? (body !== undefined ? JSON.stringify(body) : undefined) });
  };
  let res = await send(auth ? await getAccessToken() : null);
  if (res.status === 401 && auth) {
    const fresh = await refreshAccess();
    if (!fresh) {
      await signOut();
      throw new ApiError(401, { detail: 'Please sign in again.' });
    }
    res = await send(fresh);
  }
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) throw new ApiError(res.status, data);
  return data as T;
}

export async function login(username: string, password: string) {
  const data = await api<{ access: string; refresh: string }>('/api/auth/token/', {
    body: { username, password },
    auth: false,
  });
  await saveTokens(data.access, data.refresh);
  onAuthChange?.(true);
}
