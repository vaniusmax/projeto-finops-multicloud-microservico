"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/contexts/AuthContext";

export function VerifyEmailPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isReady, verifyEmail } = useAuth();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const token = searchParams.get("token") || "";

  useEffect(() => {
    if (!isReady || !isAuthenticated) return;
    router.replace("/overview");
  }, [isAuthenticated, isReady, router]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) {
      setErrorMessage("Token de ativação não encontrado.");
      return;
    }
    if (password !== confirmPassword) {
      setErrorMessage("A confirmação da senha não confere.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage("");
    try {
      await verifyEmail({ token, password });
      router.replace("/overview");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Não foi possível ativar sua conta.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[linear-gradient(180deg,_#f1fbf8_0%,_#f8fafc_100%)] px-6 py-8">
      <div className="w-full max-w-lg rounded-[32px] border border-emerald-100 bg-white p-8 shadow-2xl">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-emerald-700">Ativação Algar</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">Defina sua senha</h1>
        <p className="mt-3 text-sm leading-6 text-slate-500">
          Finalize o cadastro recebido por e-mail para liberar o acesso ao dashboard FinOps Multicloud.
        </p>

        {errorMessage ? <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{errorMessage}</div> : null}

        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <label className="block space-y-2">
            <span className="text-sm font-medium text-slate-700">Senha</span>
            <Input type="password" value={password} onChange={(event) => setPassword(event.target.value)} minLength={8} required />
          </label>
          <label className="block space-y-2">
            <span className="text-sm font-medium text-slate-700">Confirmar senha</span>
            <Input type="password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} minLength={8} required />
          </label>
          <Button type="submit" className="h-11 w-full bg-[#145A32] hover:bg-[#1E8449]" disabled={isSubmitting}>
            {isSubmitting ? "Ativando..." : "Ativar conta"}
          </Button>
        </form>
      </div>
    </div>
  );
}
