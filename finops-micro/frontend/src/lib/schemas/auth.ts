import { z } from "zod";

export const authUserSchema = z.object({
  userId: z.string(),
  firstName: z.string(),
  lastName: z.string(),
  email: z.string().email(),
  isEmailVerified: z.boolean(),
});

export const authSessionSchema = z.object({
  accessToken: z.string(),
  expiresAt: z.string().datetime(),
  user: authUserSchema,
});

export const authRegisterSchema = z.object({
  status: z.string(),
  email: z.string().email(),
  message: z.string(),
});

export type AuthUser = z.infer<typeof authUserSchema>;
export type AuthSession = z.infer<typeof authSessionSchema>;
export type AuthRegisterResponse = z.infer<typeof authRegisterSchema>;
