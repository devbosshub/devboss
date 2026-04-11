import "@/app/globals.css";

import { ReactNode } from "react";

export const metadata = {
  title: "Dev Boss",
  description: "AI engineering operations dashboard"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
