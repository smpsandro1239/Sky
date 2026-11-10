import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SKY — Descobre a tua próxima viagem",
  description: "Planeia, compara e acompanha oportunidades de viagem com a SKY.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="pt-PT"><body>{children}</body></html>;
}
