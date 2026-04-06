import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "CodeLens",
  description: "GraphRAG-powered code intelligence platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
