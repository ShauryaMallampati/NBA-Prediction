import type { Metadata } from "next"
import { GeistSans } from "geist/font/sans"
import { GeistMono } from "geist/font/mono"
import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { QueryProvider } from "@/lib/providers"
import { Sidebar } from "@/components/layout/sidebar"
import { MobileNav } from "@/components/layout/mobile-nav"

export const metadata: Metadata = {
  title: "NBA Intel — ML Game Predictions",
  description: "Ensemble machine learning predictions for NBA games. XGBoost, LightGBM, CatBoost voting with SHAP explanations.",
  keywords: ["NBA", "predictions", "machine learning", "sports analytics", "basketball"],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning className={`${GeistSans.variable} ${GeistMono.variable}`}>
      <body className="font-sans antialiased">
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem
          disableTransitionOnChange
        >
          <QueryProvider>
            <div className="min-h-screen bg-background texture-paper">
              {/* Sidebar (desktop) */}
              <Sidebar />

              {/* Mobile navigation */}
              <MobileNav />

              {/* Main content area */}
              <main className="lg:pl-64 pt-16 lg:pt-0">
                {children}
              </main>
            </div>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
