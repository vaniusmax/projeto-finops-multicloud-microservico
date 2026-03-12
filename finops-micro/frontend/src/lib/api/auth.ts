import { request } from "@/lib/api/http";
import {
  authRegisterSchema,
  authSessionSchema,
  authUserSchema,
  type AuthRegisterResponse,
  type AuthSession,
  type AuthUser,
} from "@/lib/schemas/auth";

export type RegisterPayload = {
  first_name: string;
  last_name: string;
  email: string;
};

export type LoginPayload = {
  email: string;
  password: string;
};

export type VerifyEmailPayload = {
  token: string;
  password: string;
};

export async function postRegister(payload: RegisterPayload): Promise<AuthRegisterResponse> {
  const data = await request<unknown>({ method: "POST", path: "/auth/register", body: payload });
  return authRegisterSchema.parse(data);
}

export async function postLogin(payload: LoginPayload): Promise<AuthSession> {
  const data = await request<unknown>({ method: "POST", path: "/auth/login", body: payload });
  return authSessionSchema.parse(data);
}

export async function postVerifyEmail(payload: VerifyEmailPayload): Promise<AuthSession> {
  const data = await request<unknown>({ method: "POST", path: "/auth/verify-email", body: payload });
  return authSessionSchema.parse(data);
}

export async function getMe(): Promise<AuthUser> {
  const data = await request<unknown>({ path: "/auth/me" });
  return authUserSchema.parse(data);
}

export async function postLogout(): Promise<void> {
  await request({ method: "POST", path: "/auth/logout" });
}
