"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

export function NavHeader() {
  const pathname = usePathname()

  const navItems = [
    { href: "/", label: "Home" },
    { href: "/schedule", label: "Schedule" },
    { href: "/live", label: "Live" },
    { href: "/postgame", label: "Postgame" },
    { href: "/chemistry", label: "Chemistry" },
    { href: "/sentiment", label: "Sentiment" },
  ]

  return (
    <header className="border-b border-border bg-card/50 backdrop-blur sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between py-4">
          <Link href="/" className="text-2xl font-bold hover:text-primary transition-colors">
            🏀 NBA Intelligence
          </Link>

          <nav className="hidden md:flex items-center gap-6">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`text-sm font-medium transition-colors hover:text-primary ${
                  pathname === item.href ? "text-primary" : "text-muted-foreground"
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </div>
    </header>
  )
}
