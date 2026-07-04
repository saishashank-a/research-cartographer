import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Research Cartographer",
  description: "Map an entire ML research field from a single search.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
