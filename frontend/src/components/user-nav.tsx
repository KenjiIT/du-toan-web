"use client";

import { useAuth } from "@/lib/auth";
import { useRouter } from "next/navigation";
import Link from "next/link";

export function UserNav() {
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const router = useRouter();

  if (isLoading) return null;

  if (!isAuthenticated) {
    return (
      <div className="mt-auto pt-4 border-t">
        <Link
          href="/login"
          className="block rounded-md px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground transition-colors text-center"
        >
          Đăng nhập
        </Link>
      </div>
    );
  }

  return (
    <div className="mt-auto pt-4 border-t space-y-1">
      <div className="px-3 py-2">
        <p className="text-sm font-medium truncate">{user?.full_name || user?.username}</p>
        <p className="text-xs text-muted-foreground truncate">{user?.email || user?.role}</p>
      </div>
      <Link
        href="/profile"
        className="block rounded-md px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground transition-colors"
      >
        Thông tin tài khoản
      </Link>
      <button
        onClick={() => { logout(); router.push("/"); }}
        className="w-full text-left rounded-md px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground transition-colors text-red-600"
      >
        Đăng xuất
      </button>
    </div>
  );
}
