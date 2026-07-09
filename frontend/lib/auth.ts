const AUTH_BASE = "https://10xunlock.com/api/auth";

export type AuthUser = {
  id: number;
  email: string;
};

export type LoginResponse = {
  token: string;
  user: AuthUser;
};

export async function login(email: string, password: string): Promise<LoginResponse> {
  const res = await fetch(`${AUTH_BASE}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Login failed (${res.status})`);
  }

  const data: LoginResponse = await res.json();
  localStorage.setItem("token", data.token);
  return data;
}

export async function validateToken(): Promise<AuthUser | null> {
  const token = localStorage.getItem("token");
  if (!token) return null;

  try {
    const res = await fetch(`${AUTH_BASE}/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!res.ok) {
      localStorage.removeItem("token");
      return null;
    }

    const { user } = await res.json();
    return user as AuthUser;
  } catch {
    return null;
  }
}

export async function logout(): Promise<void> {
  const token = localStorage.getItem("token");
  try {
    await fetch(`${AUTH_BASE}/logout`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  } catch {
    // best-effort
  }
  localStorage.removeItem("token");
}

export function getToken(): string | null {
  return localStorage.getItem("token");
}
