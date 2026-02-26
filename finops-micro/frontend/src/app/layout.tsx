import "@/styles/globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "FinOps Micro Dashboard",
  description: "Dashboard FinOps multicloud",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
