import "@/app/globals.css";

import { ReactNode } from "react";
import { AuthGuard } from "@/components/auth-guard";

export const metadata = {
  title: "Dev Boss",
  description: "AI engineering operations dashboard"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <AuthGuard>{children}</AuthGuard>
      </body>
    </html>
  );
}
