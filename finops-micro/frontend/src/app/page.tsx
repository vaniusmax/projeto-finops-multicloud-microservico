import Link from "next/link";

export default function HomePage() {
  return (
    <main className="container">
      <div className="panel" style={{ padding: "1.5rem" }}>
        <h1>FinOps Micro</h1>
        <p>Painel MVP baseado em API REST FastAPI.</p>
        <Link href="/dashboard">Abrir dashboard</Link>
      </div>
    </main>
  );
}
