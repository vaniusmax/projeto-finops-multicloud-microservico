"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/contexts/AuthContext";

type Mode = "login" | "register";

export function AuthPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isReady, login, register } = useAuth();
  const [mode, setMode] = useState<Mode>("login");
  const [loginForm, setLoginForm] = useState({ email: "", password: "" });
  const [registerForm, setRegisterForm] = useState({ first_name: "", last_name: "", email: "" });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  useEffect(() => {
    if (!isReady || !isAuthenticated) return;
    router.replace(searchParams.get("next") || "/overview");
  }, [isAuthenticated, isReady, router, searchParams]);

  async function handleLoginSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setErrorMessage("");
    setSuccessMessage("");
    try {
      await login(loginForm);
      router.replace(searchParams.get("next") || "/overview");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Não foi possível autenticar.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleRegisterSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setErrorMessage("");
    setSuccessMessage("");
    try {
      const result = await register(registerForm);
      setSuccessMessage(result.message);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Não foi possível concluir o cadastro.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(0,188,170,0.18),_transparent_28%),linear-gradient(135deg,_#effaf8_0%,_#f8fafc_45%,_#e8f8f3_100%)] px-6 py-8">
      <div className="mx-auto grid min-h-[calc(100vh-4rem)] max-w-7xl overflow-hidden rounded-[32px] border border-white/70 bg-white/80 shadow-2xl backdrop-blur lg:grid-cols-[1.15fr_0.85fr]">
        <section className="relative hidden overflow-hidden bg-[linear-gradient(135deg,_#0d5c56_0%,_#11b7aa_55%,_#66f0d1_100%)] p-10 text-white lg:flex lg:flex-col lg:justify-between">
          <div className="absolute -left-20 top-12 h-80 w-80 rounded-[38%_62%_65%_35%/42%_42%_58%_58%] bg-white/12 blur-sm" />
          <div className="absolute bottom-[-5rem] left-[-4rem] h-72 w-[28rem] rounded-[46%_54%_51%_49%/58%_47%_53%_42%] bg-[#49efd1]/45" />
          <div className="absolute right-[-3rem] top-[-2rem] h-72 w-72 rounded-full border border-white/30" />
          <div className="relative">
            <div className="inline-flex items-center gap-3 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-medium uppercase tracking-[0.24em]">
              Algar FinOps
            </div>
            <div className="mt-12 max-w-xl">
              <h1 className="text-6xl font-semibold tracking-tight">Algar</h1>
              <div className="mt-4 h-3 w-24 rounded-full bg-white/75" />
              <p className="mt-10 text-4xl font-semibold leading-tight text-white/95">
                Acesso corporativo ao dashboard multicloud com identidade Algar.
              </p>
              <p className="mt-6 max-w-lg text-lg leading-8 text-white/84">
                O cadastro é restrito a domínios Algar. Após solicitar acesso, você recebe por e-mail o link para ativar a conta e definir sua senha.
              </p>
            </div>
          </div>

          <div className="relative mt-12 grid gap-4 text-sm text-white/85 xl:grid-cols-3">
            <div className="rounded-2xl border border-white/15 bg-black/10 p-4 backdrop-blur">
              <p className="text-xs uppercase tracking-[0.3em] text-white/60">Acesso</p>
              <p className="mt-2 text-lg font-semibold">Somente usuários Algar</p>
            </div>
            <div className="rounded-2xl border border-white/15 bg-black/10 p-4 backdrop-blur">
              <p className="text-xs uppercase tracking-[0.3em] text-white/60">Ativação</p>
              <p className="mt-2 text-lg font-semibold">Confirmação por e-mail</p>
            </div>
            <div className="rounded-2xl border border-white/15 bg-black/10 p-4 backdrop-blur">
              <p className="text-xs uppercase tracking-[0.3em] text-white/60">Dashboard</p>
              <p className="mt-2 text-lg font-semibold">Workspace protegido</p>
            </div>
          </div>
        </section>

        <section className="flex items-center justify-center p-6 md:p-10">
          <div className="w-full max-w-md">
            <div className="mb-8 space-y-3">
              <div className="inline-flex rounded-full border border-slate-200 bg-slate-50 p-1">
                <button
                  type="button"
                  onClick={() => {
                    setMode("login");
                    setErrorMessage("");
                    setSuccessMessage("");
                  }}
                  className={`rounded-full px-4 py-2 text-sm font-semibold transition ${mode === "login" ? "bg-[#145A32] text-white" : "text-slate-600"}`}
                >
                  Entrar
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setMode("register");
                    setErrorMessage("");
                    setSuccessMessage("");
                  }}
                  className={`rounded-full px-4 py-2 text-sm font-semibold transition ${mode === "register" ? "bg-[#145A32] text-white" : "text-slate-600"}`}
                >
                  Cadastrar
                </button>
              </div>
              <div>
                <h2 className="text-3xl font-semibold tracking-tight text-slate-950">
                  {mode === "login" ? "Entrar no dashboard" : "Solicitar acesso"}
                </h2>
                <p className="mt-2 text-sm leading-6 text-slate-500">
                  {mode === "login"
                    ? "Use seu e-mail corporativo Algar e a senha definida na ativação."
                    : "Informe nome, sobrenome e e-mail Algar. O link de ativação será enviado para o endereço cadastrado."}
                </p>
              </div>
            </div>

            {errorMessage ? <div className="mb-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{errorMessage}</div> : null}
            {successMessage ? <div className="mb-4 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{successMessage}</div> : null}

            {mode === "login" ? (
              <form className="space-y-4" onSubmit={handleLoginSubmit}>
                <label className="block space-y-2">
                  <span className="text-sm font-medium text-slate-700">E-mail corporativo</span>
                  <Input
                    type="email"
                    value={loginForm.email}
                    onChange={(event) => setLoginForm((current) => ({ ...current, email: event.target.value }))}
                    placeholder="nome.sobrenome@algar.com.br"
                    required
                  />
                </label>
                <label className="block space-y-2">
                  <span className="text-sm font-medium text-slate-700">Senha</span>
                  <Input
                    type="password"
                    value={loginForm.password}
                    onChange={(event) => setLoginForm((current) => ({ ...current, password: event.target.value }))}
                    placeholder="Digite sua senha"
                    required
                  />
                </label>
                <Button type="submit" className="h-11 w-full bg-[#145A32] hover:bg-[#1E8449]" disabled={isSubmitting}>
                  {isSubmitting ? "Entrando..." : "Entrar"}
                </Button>
              </form>
            ) : (
              <form className="space-y-4" onSubmit={handleRegisterSubmit}>
                <label className="block space-y-2">
                  <span className="text-sm font-medium text-slate-700">Nome</span>
                  <Input
                    value={registerForm.first_name}
                    onChange={(event) => setRegisterForm((current) => ({ ...current, first_name: event.target.value }))}
                    placeholder="Seu nome"
                    required
                  />
                </label>
                <label className="block space-y-2">
                  <span className="text-sm font-medium text-slate-700">Sobrenome</span>
                  <Input
                    value={registerForm.last_name}
                    onChange={(event) => setRegisterForm((current) => ({ ...current, last_name: event.target.value }))}
                    placeholder="Seu sobrenome"
                    required
                  />
                </label>
                <label className="block space-y-2">
                  <span className="text-sm font-medium text-slate-700">E-mail corporativo</span>
                  <Input
                    type="email"
                    value={registerForm.email}
                    onChange={(event) => setRegisterForm((current) => ({ ...current, email: event.target.value }))}
                    placeholder="nome.sobrenome@algar.com.br"
                    required
                  />
                </label>
                <Button type="submit" className="h-11 w-full bg-[#145A32] hover:bg-[#1E8449]" disabled={isSubmitting}>
                  {isSubmitting ? "Enviando..." : "Solicitar acesso"}
                </Button>
              </form>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
