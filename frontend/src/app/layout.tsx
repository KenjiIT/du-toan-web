import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import "./globals.css";
import { Providers } from "./providers";
import { UserNav } from "@/components/user-nav";

const inter = Inter({ subsets: ["latin", "vietnamese"] });

export const metadata: Metadata = {
  title: "Dự Toán Web",
  description: "Phần mềm dự toán xây dựng trực tuyến",
};

const navItems = [
  { href: "/", label: "Trang chủ" },
  { href: "/don-gia", label: "Tra cứu đơn giá" },
  { href: "/du-toan", label: "Lập dự toán" },
  { href: "/vat-tu", label: "Vật tư" },
  { href: "/van-chuyen", label: "Vận chuyển" },
  { href: "/so-sanh", label: "So sánh giá" },
  { href: "/svdt", label: "Suất vốn đầu tư" },
  { href: "/coefficients", label: "Hệ số điều chỉnh" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi" className={`${inter.className} h-full antialiased`} data-theme="light" style={{ colorScheme: "light" }}>
      <body className="min-h-full flex">
        <Providers>
          <aside className="w-56 shrink-0 border-r bg-muted/40 p-4 flex flex-col gap-1">
            <Link href="/" className="font-bold text-lg mb-4 px-2">
              Dự Toán Web
            </Link>
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-md px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground transition-colors"
              >
                {item.label}
              </Link>
            ))}
            <UserNav />
          </aside>
          <main className="flex-1 p-6 overflow-auto">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
